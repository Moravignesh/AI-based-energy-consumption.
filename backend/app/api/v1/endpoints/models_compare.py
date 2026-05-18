from fastapi import APIRouter
from app.ml.forecasting import compare_models, run_forecast
from app.services.data_store import data_store
from app.database import get_db, ModelAccuracy
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.logging import get_logger
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)


@router.get("/compare", summary="Compare forecasting model accuracy")
def model_compare(
    device_id: str = "ALL",
    horizon:   str = "24h",
    db: Session = Depends(get_db),
):
    """
    Runs Linear Regression and ARIMA side-by-side and returns:
    MAE, RMSE, accuracy %, training time, and sample forecast points.
    Persists accuracy metrics to database.
    """
    df     = data_store.require()
    result = compare_models(df, device_id=device_id, horizon=horizon)

    # Persist accuracy records
    for r in result["results"]:
        db.add(ModelAccuracy(
            model_name=r["model_name"], device_id=device_id,
            horizon=horizon, mae=r["mae"], rmse=r["rmse"],
            mape=0, accuracy_pct=r["accuracy_pct"],
            data_points=len(r["forecast_points"]),
        ))
    db.commit()
    return result


@router.get("/accuracy-history", summary="Historical model accuracy log")
def accuracy_history(limit: int = 30, db: Session = Depends(get_db)):
    """Returns the last N model accuracy measurements."""
    rows = db.query(ModelAccuracy).order_by(ModelAccuracy.created_at.desc()).limit(limit).all()
    return {"records": [
        {"model_name": r.model_name, "device_id": r.device_id,
         "horizon": r.horizon, "mae": r.mae, "rmse": r.rmse,
         "accuracy_pct": r.accuracy_pct, "data_points": r.data_points,
         "created_at": r.created_at.isoformat()}
        for r in rows
    ]}
