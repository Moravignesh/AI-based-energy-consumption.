from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.schemas import AlertCreate, AlertResponse, AlertsCountResponse, SuccessResponse
from app.services import alert_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", summary="List all alerts")
def list_alerts(
    severity:   Optional[str] = Query(None, enum=["low","medium","high","critical"]),
    is_read:    Optional[bool] = None,
    is_resolved:Optional[bool] = None,
    skip:       int = Query(0, ge=0),
    limit:      int = Query(50, ge=1, le=200),
    db:         Session = Depends(get_db),
):
    """Paginated, filterable list of platform alerts."""
    alerts = alert_service.get_alerts(
        db, severity=severity, is_read=is_read,
        is_resolved=is_resolved, skip=skip, limit=limit,
    )
    return {"alerts": [_fmt(a) for a in alerts], "count": len(alerts)}


@router.post("/", summary="Create a manual alert")
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    """Manually create a platform alert."""
    alert = alert_service.create_alert(db, payload)
    return _fmt(alert)


@router.get("/counts", summary="Alert count summary")
def alert_counts(db: Session = Depends(get_db)):
    """Returns total, unread, unresolved, and per-severity counts."""
    return alert_service.get_alert_counts(db)


@router.get("/{alert_id}", summary="Get alert by ID")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = alert_service.get_alert_by_id(db, alert_id)
    if not a:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return _fmt(a)


@router.patch("/{alert_id}/read", summary="Mark alert as read")
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    a = alert_service.mark_read(db, alert_id)
    if not a:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return _fmt(a)


@router.patch("/{alert_id}/resolve", summary="Resolve an alert")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    a = alert_service.resolve_alert(db, alert_id)
    if not a:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return _fmt(a)


@router.post("/mark-all-read", summary="Mark all alerts as read")
def mark_all_read(db: Session = Depends(get_db)):
    n = alert_service.mark_all_read(db)
    return SuccessResponse(message=f"Marked {n} alerts as read.")


@router.delete("/{alert_id}", summary="Delete an alert")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    ok = alert_service.delete_alert(db, alert_id)
    if not ok:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return SuccessResponse(message=f"Alert {alert_id} deleted.")


def _fmt(a):
    return {
        "id": a.id, "alert_type": a.alert_type, "severity": a.severity,
        "title": a.title, "message": a.message, "device_id": a.device_id,
        "building_id": a.building_id, "is_read": a.is_read,
        "is_resolved": a.is_resolved,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "created_at": a.created_at.isoformat(),
    }
