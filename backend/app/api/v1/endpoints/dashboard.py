from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd, numpy as np
from datetime import datetime

from app.services.data_store import data_store
from app.ml.forecasting import run_forecast
from app.ml.anomaly import run_anomaly_detection
from app.ml.optimization import run_optimization, _peak_analysis
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
RATE = settings.ELECTRICITY_RATE_USD_KWH

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
DAY_NAMES   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


@router.get("/summary", summary="Dashboard KPI summary")
def summary():
    """
    Returns all key performance indicators for the main dashboard:
    consumption totals, cost estimates, trend, peak hours, anomaly count, and forecasts.
    """
    df = data_store.require()
    total = float(df["energy_kwh"].sum())
    days  = max(1, (df["timestamp"].max() - df["timestamp"].min()).days)

    hourly_avg = df.groupby(df["timestamp"].dt.hour)["energy_kwh"].mean()
    peak_hour  = int(hourly_avg.idxmax())
    opeak_hour = int(hourly_avg.idxmin())

    # 7-day trend
    cut7 = df["timestamp"].max() - pd.Timedelta(days=7)
    cut14= cut7 - pd.Timedelta(days=7)
    last7 = df[df["timestamp"] >= cut7]["energy_kwh"].sum()
    prev7 = df[(df["timestamp"] >= cut14) & (df["timestamp"] < cut7)]["energy_kwh"].sum()
    trend_pct = (last7 - prev7) / (prev7 + 1e-9) * 100
    trend = "increasing" if trend_pct > 5 else ("decreasing" if trend_pct < -5 else "stable")

    # Quick anomaly count (fast z-score only)
    try:
        anom = run_anomaly_detection(df, method="zscore", sensitivity=0.05)
        anomaly_count = anom["anomaly_count"]
    except Exception:
        anomaly_count = 0

    # Savings potential
    try:
        opt = run_optimization(df)
        savings_pct = opt["savings_potential_pct"]
    except Exception:
        savings_pct = 0.0

    # 24h + 7d forecast totals
    try:
        fc24 = run_forecast(df, horizon="24h", model="auto")
        next24h = fc24["total_predicted_kwh"]
    except Exception:
        next24h = total / days

    try:
        fc7 = run_forecast(df, horizon="7d", model="auto")
        next7d = fc7["total_predicted_kwh"]
    except Exception:
        next7d = total / days * 7

    last_ts = df["timestamp"].max().isoformat()

    return {
        "total_consumption_kwh":    round(total, 2),
        "avg_daily_kwh":            round(total / days, 2),
        "avg_hourly_kwh":           round(total / (days * 24), 4),
        "peak_hour":                peak_hour,
        "peak_kwh":                 round(float(hourly_avg.max()), 4),
        "off_peak_hour":            opeak_hour,
        "off_peak_kwh":             round(float(hourly_avg.min()), 4),
        "active_devices":           int(df["device_id"].nunique()),
        "active_buildings":         int(df["building_id"].nunique()) if "building_id" in df.columns else 1,
        "anomaly_count":            anomaly_count,
        "unread_alerts":            anomaly_count,
        "forecast_next_24h_kwh":    round(next24h, 2),
        "forecast_next_7d_kwh":     round(next7d, 2),
        "estimated_daily_cost_usd": round(total / days * RATE, 2),
        "estimated_monthly_cost_usd": round(total / days * 30 * RATE, 2),
        "estimated_annual_cost_usd":  round(total / days * 365 * RATE, 2),
        "consumption_trend":        trend,
        "trend_pct":                round(float(trend_pct), 1),
        "savings_potential_pct":    round(savings_pct, 1),
        "data_days":                days,
        "last_reading_at":          last_ts,
    }


@router.get("/historical", summary="Historical time-series data")
def historical(
    device_id:  str = "ALL",
    resolution: str = Query("hourly", enum=["hourly", "daily", "weekly"]),
    limit:      int = Query(500, ge=10, le=5000),
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
):
    """
    Historical consumption data for rendering charts.
    Supports hourly / daily / weekly aggregation and date range filtering.
    """
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id].copy()
    if date_from:
        df = df[df["timestamp"] >= pd.to_datetime(date_from)]
    if date_to:
        df = df[df["timestamp"] <= pd.to_datetime(date_to)]

    if resolution == "daily":
        grp = df.groupby(df["timestamp"].dt.date)["energy_kwh"].sum().reset_index()
        grp.columns = ["timestamp", "energy_kwh"]
        grp["timestamp"] = grp["timestamp"].astype(str)
        data = grp.to_dict(orient="records")
    elif resolution == "weekly":
        grp = df.set_index("timestamp").resample("W")["energy_kwh"].sum().reset_index()
        grp["timestamp"] = grp["timestamp"].dt.strftime("%Y-%m-%d")
        data = grp.to_dict(orient="records")
    else:
        grp = df.sort_values("timestamp")[["timestamp","device_id","energy_kwh"]].copy()
        if len(grp) > limit:
            grp = grp.iloc[::len(grp)//limit]
        grp["timestamp"] = grp["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        data = grp.to_dict(orient="records")

    return {"device_id": device_id, "resolution": resolution, "count": len(data), "data": data}


@router.get("/device-breakdown", summary="Per-device consumption breakdown")
def device_breakdown():
    """Returns total, average, max and share % for each device."""
    df    = data_store.require()
    total = df["energy_kwh"].sum()
    bkd   = (
        df.groupby("device_id")
        .agg(total_kwh=("energy_kwh","sum"), avg_kwh=("energy_kwh","mean"),
             max_kwh=("energy_kwh","max"), min_kwh=("energy_kwh","min"),
             std_kwh=("energy_kwh","std"), reading_count=("energy_kwh","count"))
        .reset_index().sort_values("total_kwh", ascending=False)
    )
    bkd["share_pct"]  = (bkd["total_kwh"] / total * 100).round(2)
    bkd["cost_usd"]   = (bkd["total_kwh"] * RATE).round(2)
    if "building_id" in df.columns:
        bmap = df.drop_duplicates("device_id").set_index("device_id")["building_id"]
        bkd["building_id"] = bkd["device_id"].map(bmap)
    return {"devices": bkd.fillna(0).to_dict(orient="records")}


@router.get("/hourly-pattern", summary="Average hourly consumption pattern")
def hourly_pattern(device_id: str = "ALL"):
    """24-hour average profile — useful for identifying peak/off-peak windows."""
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id]
    df = df.copy(); df["hour"] = df["timestamp"].dt.hour
    pat = df.groupby("hour")["energy_kwh"].agg(["mean","max","min","std"]).reset_index()
    pat.columns = ["hour","avg_kwh","max_kwh","min_kwh","std_kwh"]
    pat = pat.fillna(0).round(4)
    return {"device_id": device_id, "pattern": pat.to_dict(orient="records")}


@router.get("/weekly-pattern", summary="Average consumption by day of week")
def weekly_pattern(device_id: str = "ALL"):
    """Mon–Sun average profile to compare weekday vs. weekend load."""
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id]
    df = df.copy(); df["dow"] = df["timestamp"].dt.dayofweek
    pat = df.groupby("dow")["energy_kwh"].agg(["mean","max"]).reset_index()
    pat.columns = ["day_of_week","avg_kwh","max_kwh"]
    pat["day_name"] = pat["day_of_week"].apply(lambda d: DAY_NAMES[d])
    return {"device_id": device_id, "pattern": pat.round(4).to_dict(orient="records")}


@router.get("/monthly-trend", summary="Monthly consumption trend")
def monthly_trend(device_id: str = "ALL"):
    """Month-by-month aggregated consumption, cost, and daily average."""
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id]
    df = df.copy()
    df["year"]  = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month

    grp = df.groupby(["year","month"])["energy_kwh"].agg(["sum","mean"]).reset_index()
    grp.columns = ["year","month","total_kwh","avg_hourly_kwh"]
    grp["avg_daily_kwh"] = grp["avg_hourly_kwh"] * 24
    grp["cost_usd"]      = (grp["total_kwh"] * RATE).round(2)
    grp["month_name"]    = grp["month"].apply(lambda m: MONTH_NAMES[m-1])
    return {"device_id": device_id, "trend": grp.round(4).to_dict(orient="records")}


@router.get("/cost-analysis", summary="Detailed cost analysis")
def cost_analysis():
    """
    Breakdown of energy costs by period, device, and building.
    Uses configurable electricity rate (default $0.12/kWh).
    """
    df    = data_store.require()
    total = float(df["energy_kwh"].sum())
    days  = max(1, (df["timestamp"].max() - df["timestamp"].min()).days)

    peak  = _peak_analysis(df)
    ph    = peak["peak_hours"]

    df["is_peak"] = df["timestamp"].dt.hour.isin(ph)
    peak_kwh   = float(df[df["is_peak"]]["energy_kwh"].sum())
    offpeak_kwh= float(df[~df["is_peak"]]["energy_kwh"].sum())

    cost_by_dev = (
        df.groupby("device_id")["energy_kwh"].sum()
        .apply(lambda k: round(float(k) * RATE, 2))
        .reset_index().rename(columns={"energy_kwh":"cost_usd"})
        .to_dict(orient="records")
    )

    cost_by_bld = []
    if "building_id" in df.columns:
        cost_by_bld = (
            df.groupby("building_id")["energy_kwh"].sum()
            .apply(lambda k: round(float(k) * RATE, 2))
            .reset_index().rename(columns={"energy_kwh":"cost_usd"})
            .to_dict(orient="records")
        )

    return {
        "rate_usd_kwh":     RATE,
        "daily_cost_usd":   round(total / days * RATE, 2),
        "weekly_cost_usd":  round(total / days * 7 * RATE, 2),
        "monthly_cost_usd": round(total / days * 30 * RATE, 2),
        "annual_cost_usd":  round(total / days * 365 * RATE, 2),
        "peak_cost_usd":    round(peak_kwh * RATE, 2),
        "off_peak_cost_usd":round(offpeak_kwh * RATE, 2),
        "peak_hours":       ph,
        "cost_by_device":   cost_by_dev,
        "cost_by_building": cost_by_bld,
    }


@router.get("/statistics", summary="Descriptive statistics of the dataset")
def statistics(device_id: str = "ALL"):
    """Full descriptive statistics: percentiles, skewness, kurtosis."""
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id]
    s = df["energy_kwh"].describe(percentiles=[.1,.25,.5,.75,.9,.99]).to_dict()
    s["skewness"]  = float(df["energy_kwh"].skew())
    s["kurtosis"]  = float(df["energy_kwh"].kurtosis())
    s["total_kwh"] = float(df["energy_kwh"].sum())
    return {"device_id": device_id, "statistics": {k: round(v,4) for k,v in s.items()}}
