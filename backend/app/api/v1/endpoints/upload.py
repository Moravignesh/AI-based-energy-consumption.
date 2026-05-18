from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import pandas as pd, io

from app.database import get_db, EnergyReading
from app.models.schemas import UploadResponse, UploadStatusResponse, SuccessResponse
from app.services.data_store import data_store
from app.utils.preprocessing import validate_and_clean
from app.core.exceptions import EnergyPlatformError
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _persist(df: pd.DataFrame, db: Session):
    db.query(EnergyReading).delete()
    batch = []
    for _, r in df.iterrows():
        batch.append(EnergyReading(
            timestamp=r["timestamp"], device_id=str(r["device_id"]),
            building_id=str(r.get("building_id", "Unknown")),
            energy_kwh=float(r["energy_kwh"]),
            temperature=float(r["temperature"]) if pd.notna(r.get("temperature")) else None,
            humidity=float(r["humidity"]) if pd.notna(r.get("humidity")) else None,
            occupancy=int(r["occupancy"]) if pd.notna(r.get("occupancy")) else None,
        ))
        if len(batch) >= 500:
            db.bulk_save_objects(batch); db.commit(); batch = []
    if batch:
        db.bulk_save_objects(batch); db.commit()
    logger.info(f"Persisted {len(df):,} records to DB")


@router.post("/csv", response_model=UploadResponse, summary="Upload energy CSV")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an energy-consumption CSV file.

    **Required columns:** `timestamp`, `energy_kwh`

    **Optional columns:** `device_id`, `building_id`, `temperature`, `humidity`, `occupancy`
    """
    if not file.filename.lower().endswith(".csv"):
        raise EnergyPlatformError("Only CSV files (.csv) are supported.", 400)

    content = await file.read()
    try:
        raw = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise EnergyPlatformError(f"Could not parse CSV: {e}", 400)

    try:
        df, warnings = validate_and_clean(raw)
    except ValueError as e:
        raise EnergyPlatformError(str(e), 422)

    data_store.set(df, file.filename)
    background_tasks.add_task(_persist, df, db)
    meta = data_store.meta

    return UploadResponse(
        status="success", filename=file.filename,
        records=meta["records"], devices=meta["devices"],
        buildings=meta["buildings"], date_range=meta["date_range"],
        columns=meta["columns"], warnings=warnings,
    )


@router.post("/generate-sample", response_model=UploadResponse, summary="Generate synthetic sample data")
async def generate_sample(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Generate 6 months of realistic synthetic energy data for 5 devices."""
    from app.utils.data_generator import generate
    from app.utils.preprocessing import validate_and_clean

    raw = generate(start="2024-01-01", end="2024-06-30")
    df, warnings = validate_and_clean(raw)
    data_store.set(df, "sample_generated_data.csv")
    background_tasks.add_task(_persist, df, db)
    meta = data_store.meta

    return UploadResponse(
        status="success", filename="sample_generated_data.csv",
        records=meta["records"], devices=meta["devices"],
        buildings=meta["buildings"], date_range=meta["date_range"],
        columns=meta["columns"],
        warnings=["This is synthetic data generated for demonstration purposes."],
    )


@router.get("/status", response_model=UploadStatusResponse, summary="Check loaded dataset status")
def upload_status():
    """Returns metadata about the currently loaded dataset."""
    if not data_store.is_loaded:
        return UploadStatusResponse(loaded=False)
    m = data_store.meta
    return UploadStatusResponse(
        loaded=True, filename=data_store.filename,
        records=m["records"], devices=m["devices"],
        buildings=m["buildings"], date_range=m["date_range"],
        columns=m["columns"],
    )


@router.delete("/clear", response_model=SuccessResponse, summary="Clear loaded dataset")
def clear_data(db: Session = Depends(get_db)):
    """Remove all in-memory and persisted energy data."""
    data_store.clear()
    db.query(EnergyReading).delete(); db.commit()
    return SuccessResponse(message="Dataset cleared successfully.")
