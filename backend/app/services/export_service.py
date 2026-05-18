"""
Export Service — generates downloadable CSV / JSON reports.
"""
import io
import json
import pandas as pd
from datetime import datetime
from typing import Optional, List
from app.core.logging import get_logger

logger = get_logger(__name__)


def export_dataframe_csv(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    device_id: Optional[str] = None,
) -> bytes:
    """Filter and serialise DataFrame to CSV bytes."""
    out = df.copy()

    if device_id and device_id != "ALL":
        out = out[out["device_id"] == device_id]
    if date_from:
        out = out[out["timestamp"] >= pd.to_datetime(date_from)]
    if date_to:
        out = out[out["timestamp"] <= pd.to_datetime(date_to)]
    if columns:
        valid = [c for c in columns if c in out.columns]
        if valid:
            out = out[valid]

    out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def build_summary_report(
    df: pd.DataFrame,
    anomaly_result: Optional[dict] = None,
    optimization_result: Optional[dict] = None,
) -> dict:
    """Compose a comprehensive JSON summary report."""
    total_kwh = float(df["energy_kwh"].sum())
    days = max(1, (df["timestamp"].max() - df["timestamp"].min()).days)
    rate = 0.12

    device_breakdown = (
        df.groupby("device_id")["energy_kwh"]
        .agg(["sum", "mean", "max"])
        .rename(columns={"sum": "total_kwh", "mean": "avg_kwh", "max": "peak_kwh"})
        .reset_index()
        .to_dict(orient="records")
    )

    top_device = max(device_breakdown, key=lambda x: x["total_kwh"], default={})

    return {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "period_start": df["timestamp"].min().isoformat(),
            "period_end": df["timestamp"].max().isoformat(),
            "data_days": days,
            "total_records": len(df),
        },
        "consumption_summary": {
            "total_kwh": round(total_kwh, 2),
            "avg_daily_kwh": round(total_kwh / days, 2),
            "avg_hourly_kwh": round(total_kwh / (days * 24), 4),
            "peak_device": top_device.get("device_id", "N/A"),
            "peak_device_kwh": round(top_device.get("total_kwh", 0), 2),
            "device_count": int(df["device_id"].nunique()),
        },
        "cost_summary": {
            "total_cost_usd": round(total_kwh * rate, 2),
            "daily_cost_usd": round(total_kwh / days * rate, 2),
            "monthly_cost_usd": round(total_kwh / days * 30 * rate, 2),
            "annual_cost_usd": round(total_kwh / days * 365 * rate, 2),
            "rate_usd_kwh": rate,
        },
        "device_breakdown": device_breakdown,
        "anomaly_summary": {
            "total_anomalies": anomaly_result.get("anomaly_count", 0) if anomaly_result else None,
            "anomaly_rate_pct": anomaly_result.get("anomaly_rate_pct", 0) if anomaly_result else None,
            "anomaly_types": anomaly_result.get("anomaly_types", {}) if anomaly_result else {},
        },
        "optimization_summary": {
            "savings_potential_kwh": optimization_result.get("total_potential_savings_kwh") if optimization_result else None,
            "savings_potential_usd": optimization_result.get("total_potential_savings_usd") if optimization_result else None,
            "top_recommendations": [
                r["title"] for r in (optimization_result or {}).get("recommendations", [])[:3]
            ],
        },
    }


def report_to_csv(report: dict) -> bytes:
    """Flatten report dict to a readable CSV."""
    rows = []
    for section, values in report.items():
        if isinstance(values, dict):
            for k, v in values.items():
                if not isinstance(v, (list, dict)):
                    rows.append({"Section": section, "Metric": k, "Value": v})
        elif isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    item["_section"] = section
                    rows.append(item)

    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
