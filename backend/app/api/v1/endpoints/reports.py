from fastapi import APIRouter, Query
from fastapi.responses import Response
from typing import Optional
from app.services.data_store import data_store
from app.services.export_service import (
    export_dataframe_csv, build_summary_report, report_to_csv
)
from app.ml.anomaly import run_anomaly_detection
from app.ml.optimization import run_optimization
from app.core.logging import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)


@router.get("/summary", summary="Generate full summary report (JSON)")
def report_summary():
    """JSON report covering consumption, costs, anomalies, and recommendations."""
    df   = data_store.require()
    try:
        anom = run_anomaly_detection(df, method="zscore", sensitivity=0.05)
    except Exception:
        anom = None
    try:
        opt  = run_optimization(df)
    except Exception:
        opt  = None
    return build_summary_report(df, anom, opt)


@router.get("/export/csv", summary="Export raw dataset as CSV")
def export_csv(
    device_id:  str = "ALL",
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
):
    """Download the loaded dataset (or filtered subset) as a CSV file."""
    df  = data_store.require()
    csv = export_dataframe_csv(df, date_from=date_from, date_to=date_to,
                                device_id=device_id if device_id != "ALL" else None)
    return Response(
        content=csv, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=energy_export.csv"},
    )


@router.get("/export/report-csv", summary="Export summary report as CSV")
def export_report_csv():
    """Download the summary report flattened to CSV."""
    df      = data_store.require()
    report  = build_summary_report(df)
    csv     = report_to_csv(report)
    return Response(
        content=csv, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=energy_report.csv"},
    )


@router.get("/export/json", summary="Export summary report as JSON file")
def export_report_json():
    """Download the full summary report as a JSON file."""
    df      = data_store.require()
    report  = build_summary_report(df)
    content = json.dumps(report, indent=2, default=str).encode()
    return Response(
        content=content, media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=energy_report.json"},
    )
