from fastapi import APIRouter, Query
from typing import List
from app.models.schemas import ForecastRequest, BatchForecastRequest
from app.ml.forecasting import run_forecast, compare_models
from app.services.data_store import data_store
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/run", summary="Run energy consumption forecast")
def forecast_run(req: ForecastRequest):
    """
    Run a forecast for a specific device or all devices combined.

    - **device_id**: Device identifier or \'ALL\'
    - **horizon**: 24h, 7d, or 30d
    - **model**: auto (best), arima, or linear
    """
    df = data_store.require()
    if req.device_id != "ALL":
        data_store.require_device(req.device_id)
    return run_forecast(df, device_id=req.device_id, horizon=req.horizon, model=req.model)


@router.post("/batch", summary="Batch forecast for multiple devices")
def forecast_batch(req: BatchForecastRequest):
    """Run forecasts for multiple device IDs in a single request."""
    df = data_store.require()
    results = []
    for dev in req.device_ids:
        try:
            r = run_forecast(df, device_id=dev, horizon=req.horizon, model=req.model)
            results.append(r)
        except Exception as e:
            results.append({"device_id": dev, "error": str(e)})
    from datetime import datetime
    return {"results": results, "total_devices": len(results),
            "horizon": req.horizon, "created_at": datetime.utcnow().isoformat()}


@router.get("/quick/{horizon}", summary="Quick forecast with default settings")
def forecast_quick(horizon: str = "24h"):
    """Quick all-device forecast. Horizon: 24h | 7d | 30d"""
    df = data_store.require()
    return run_forecast(df, device_id="ALL", horizon=horizon, model="auto")


@router.get("/devices", summary="List available devices for forecasting")
def forecast_devices():
    """Returns all device IDs plus the \'ALL\' aggregate option."""
    df = data_store.require()
    return {"devices": ["ALL"] + sorted(df["device_id"].unique().tolist())}


@router.get("/horizons", summary="List supported forecast horizons")
def forecast_horizons():
    return {"horizons": [
        {"key": "24h", "label": "Next 24 Hours",  "hours": 24},
        {"key": "7d",  "label": "Next 7 Days",    "hours": 168},
        {"key": "30d", "label": "Next 30 Days",   "hours": 720},
    ]}
