from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import AnomalyRequest
from app.ml.anomaly import run_anomaly_detection
from app.services.data_store import data_store
from app.services.alert_service import auto_generate_alerts
from app.database import get_db
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/run", summary="Run anomaly detection")
def anomaly_run(req: AnomalyRequest, db: Session = Depends(get_db)):
    """
    Detect abnormal energy consumption patterns.

    - **method**: ensemble (recommended), isolation_forest, or zscore
    - **sensitivity**: 0.01 (few alerts) to 0.30 (many alerts)
    """
    df = data_store.require()
    result = run_anomaly_detection(
        df, device_id=req.device_id,
        method=req.method, sensitivity=req.sensitivity,
    )
    # Auto-generate platform alerts for significant anomalies
    auto_generate_alerts(db, result, [])
    return result


@router.get("/quick", summary="Quick anomaly scan with defaults")
def anomaly_quick():
    """Run ensemble anomaly detection on all devices with default sensitivity."""
    df = data_store.require()
    return run_anomaly_detection(df, method="ensemble", sensitivity=0.05)


@router.get("/summary", summary="Anomaly summary statistics")
def anomaly_summary():
    """High-level anomaly stats — faster than a full run."""
    df = data_store.require()
    import pandas as pd, numpy as np
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["roll_mean"] = (df.groupby("device_id")["energy_kwh"]
                         .transform(lambda x: x.rolling(24, min_periods=4).mean().shift(1)))
    df["roll_std"]  = (df.groupby("device_id")["energy_kwh"]
                         .transform(lambda x: x.rolling(24, min_periods=4).std().shift(1).fillna(0)))
    df["zscore"]    = (df["energy_kwh"] - df["roll_mean"]) / (df["roll_std"] + 1e-6)
    df["is_anomaly"]= df["zscore"].abs() > 3.0

    by_device = (df.groupby("device_id")
                   .agg(total=("energy_kwh","count"), anomalies=("is_anomaly","sum"))
                   .reset_index())
    by_device["rate_pct"] = (by_device["anomalies"] / by_device["total"] * 100).round(2)

    return {
        "total_records":    int(len(df)),
        "anomaly_count":    int(df["is_anomaly"].sum()),
        "anomaly_rate_pct": round(float(df["is_anomaly"].mean() * 100), 2),
        "by_device":        by_device.to_dict(orient="records"),
    }


@router.get("/methods", summary="List anomaly detection methods")
def anomaly_methods():
    return {"methods": [
        {"key":"ensemble",         "label":"Ensemble (IF + Z-Score)", "description":"Best accuracy, recommended"},
        {"key":"isolation_forest", "label":"Isolation Forest",        "description":"ML-based, handles complex patterns"},
        {"key":"zscore",           "label":"Z-Score Statistical",     "description":"Fast, simple threshold-based"},
    ]}
