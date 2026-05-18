from fastapi import APIRouter, Query
import pandas as pd
from app.services.data_store import data_store
from app.ml.forecasting import run_forecast
from app.ml.anomaly import run_anomaly_detection
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
RATE = settings.ELECTRICITY_RATE_USD_KWH


@router.get("/", summary="List all devices")
def list_devices():
    """Returns a summary row for every device in the dataset."""
    df = data_store.require()
    total = float(df["energy_kwh"].sum())
    devs  = (
        df.groupby("device_id")
        .agg(total_kwh=("energy_kwh","sum"), avg_kwh=("energy_kwh","mean"),
             max_kwh=("energy_kwh","max"), min_kwh=("energy_kwh","min"),
             reading_count=("energy_kwh","count"),
             first_reading=("timestamp","min"), last_reading=("timestamp","max"))
        .reset_index()
    )
    if "building_id" in df.columns:
        bmap = df.drop_duplicates("device_id").set_index("device_id")["building_id"]
        devs["building_id"] = devs["device_id"].map(bmap)
    devs["share_pct"] = (devs["total_kwh"] / total * 100).round(2)
    devs["cost_usd"]  = (devs["total_kwh"] * RATE).round(2)
    devs["first_reading"] = devs["first_reading"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    devs["last_reading"]  = devs["last_reading"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return {"devices": devs.fillna(0).to_dict(orient="records"), "total": len(devs)}


@router.get("/{device_id}", summary="Get device details")
def device_detail(device_id: str):
    """Full stats for a single device."""
    df  = data_store.require_device(device_id)
    dfd = df.copy()
    dfd["hour"] = dfd["timestamp"].dt.hour
    dfd["dow"]  = dfd["timestamp"].dt.dayofweek

    hourly  = dfd.groupby("hour")["energy_kwh"].agg(["mean","max","min","std"]).reset_index()
    hourly.columns = ["hour","avg_kwh","max_kwh","min_kwh","std_kwh"]
    weekly  = dfd.groupby("dow")["energy_kwh"].agg(["mean","max"]).reset_index()
    weekly.columns = ["day_of_week","avg_kwh","max_kwh"]
    DAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekly["day_name"] = weekly["day_of_week"].map(lambda d: DAY_NAMES[d])

    total = float(dfd["energy_kwh"].sum())
    days  = max(1,(dfd["timestamp"].max()-dfd["timestamp"].min()).days)

    return {
        "device_id":    device_id,
        "building_id":  str(dfd["building_id"].iloc[0]) if "building_id" in dfd.columns else None,
        "stats": {
            "total_kwh":      round(total,2),
            "avg_daily_kwh":  round(total/days,2),
            "avg_hourly_kwh": round(float(dfd["energy_kwh"].mean()),4),
            "max_kwh":        round(float(dfd["energy_kwh"].max()),4),
            "min_kwh":        round(float(dfd["energy_kwh"].min()),4),
            "std_kwh":        round(float(dfd["energy_kwh"].std()),4),
            "reading_count":  len(dfd),
            "cost_usd":       round(total*RATE,2),
            "first_reading":  dfd["timestamp"].min().isoformat(),
            "last_reading":   dfd["timestamp"].max().isoformat(),
        },
        "hourly_pattern": hourly.fillna(0).round(4).to_dict(orient="records"),
        "weekly_pattern": weekly.fillna(0).round(4).to_dict(orient="records"),
    }


@router.get("/{device_id}/forecast", summary="Device-specific forecast")
def device_forecast(device_id: str, horizon: str = "24h", model: str = "auto"):
    """Run a forecast for a specific device."""
    df = data_store.require_device(device_id)
    return run_forecast(df, device_id=device_id, horizon=horizon, model=model)


@router.get("/{device_id}/anomalies", summary="Device anomaly report")
def device_anomalies(device_id: str, method: str = "ensemble", sensitivity: float = 0.05):
    """Run anomaly detection scoped to a single device."""
    df = data_store.require_device(device_id)
    return run_anomaly_detection(df, device_id=device_id, method=method, sensitivity=sensitivity)


@router.get("/{device_id}/history", summary="Device historical readings")
def device_history(
    device_id: str,
    resolution: str = Query("hourly", enum=["hourly","daily"]),
    limit: int = Query(300, ge=10, le=2000),
):
    """Historical consumption for one device."""
    df = data_store.require_device(device_id)
    if resolution == "daily":
        grp = df.groupby(df["timestamp"].dt.date)["energy_kwh"].sum().reset_index()
        grp.columns = ["timestamp","energy_kwh"]
        grp["timestamp"] = grp["timestamp"].astype(str)
        data = grp.to_dict(orient="records")
    else:
        grp = df.sort_values("timestamp")[["timestamp","energy_kwh"]].copy()
        if len(grp) > limit:
            grp = grp.iloc[::len(grp)//limit]
        grp["timestamp"] = grp["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        data = grp.to_dict(orient="records")
    return {"device_id": device_id, "resolution": resolution, "data": data}
