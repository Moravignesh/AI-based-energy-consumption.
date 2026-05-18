from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.database import get_db
from app.services.data_store import data_store
from app.core.config import settings
import time

router = APIRouter()
_START_TIME = time.time()
_COUNTERS: dict = {"forecast":0,"anomaly":0,"simulation":0,"optimization":0,"api_calls":0}


def increment(key: str):
    _COUNTERS[key] = _COUNTERS.get(key,0) + 1
    _COUNTERS["api_calls"] = _COUNTERS.get("api_calls",0) + 1


@router.get("/", summary="Basic health check")
def health_basic():
    """Returns 200 OK with service status."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/detailed", summary="Detailed system health")
def health_detailed(db: Session = Depends(get_db)):
    """Checks database connectivity, data store, and returns system info."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status":        "ok" if db_status == "connected" else "degraded",
        "version":       settings.APP_VERSION,
        "environment":   settings.APP_ENV,
        "database":      db_status,
        "data_loaded":   data_store.is_loaded,
        "record_count":  data_store.meta.get("records", 0) if data_store.is_loaded else 0,
        "uptime_seconds":round(time.time() - _START_TIME, 1),
        "timestamp":     datetime.utcnow().isoformat(),
    }


@router.get("/metrics", summary="API usage metrics")
def metrics():
    """Returns basic request and usage counters."""
    return {
        "uptime_seconds":     round(time.time() - _START_TIME, 1),
        "total_api_calls":    _COUNTERS.get("api_calls", 0),
        "forecast_runs":      _COUNTERS.get("forecast", 0),
        "anomaly_runs":       _COUNTERS.get("anomaly", 0),
        "simulation_runs":    _COUNTERS.get("simulation", 0),
        "optimization_runs":  _COUNTERS.get("optimization", 0),
    }
