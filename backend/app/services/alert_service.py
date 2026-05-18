"""
Alert Service — creates, queries and resolves platform alerts.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import Alert
from app.models.schemas import AlertCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_alert(db: Session, payload: AlertCreate) -> Alert:
    alert = Alert(
        alert_type=payload.alert_type,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        device_id=payload.device_id,
        building_id=payload.building_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(f"Alert created: [{payload.severity.upper()}] {payload.title}")
    return alert


def get_alerts(
    db: Session,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Alert]:
    q = db.query(Alert)
    if severity:
        q = q.filter(Alert.severity == severity)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    if is_read is not None:
        q = q.filter(Alert.is_read == is_read)
    if is_resolved is not None:
        q = q.filter(Alert.is_resolved == is_resolved)
    return q.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()


def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def mark_read(db: Session, alert_id: int) -> Optional[Alert]:
    alert = get_alert_by_id(db, alert_id)
    if alert:
        alert.is_read = True
        db.commit()
        db.refresh(alert)
    return alert


def mark_all_read(db: Session) -> int:
    count = db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})
    db.commit()
    return count


def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
    alert = get_alert_by_id(db, alert_id)
    if alert:
        alert.is_resolved = True
        alert.is_read = True
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: int) -> bool:
    alert = get_alert_by_id(db, alert_id)
    if alert:
        db.delete(alert)
        db.commit()
        return True
    return False


def get_alert_counts(db: Session) -> dict:
    from sqlalchemy import func
    total      = db.query(Alert).count()
    unread     = db.query(Alert).filter(Alert.is_read == False).count()
    unresolved = db.query(Alert).filter(Alert.is_resolved == False).count()
    by_severity = {}
    for sev in ("low", "medium", "high", "critical"):
        by_severity[sev] = db.query(Alert).filter(Alert.severity == sev).count()
    return {"total": total, "unread": unread, "unresolved": unresolved, "by_severity": by_severity}


def auto_generate_alerts(db: Session, anomaly_result: dict, peak_predictions: list) -> List[Alert]:
    """Auto-create alerts from anomaly detection and peak forecast results."""
    created = []

    # Anomalies
    rate = anomaly_result.get("anomaly_rate_pct", 0)
    if rate > 5:
        a = create_alert(db, AlertCreate(
            alert_type="anomaly",
            severity="high" if rate > 10 else "medium",
            title=f"High anomaly rate detected: {rate:.1f}%",
            message=(f"Anomaly detection found {anomaly_result.get('anomaly_count', 0)} abnormal readings "
                     f"({rate:.1f}% of total). Investigate devices for faults or sensor issues."),
        ))
        created.append(a)

    # Peaks
    for peak in peak_predictions:
        if peak.get("severity") in ("high", "medium"):
            a = create_alert(db, AlertCreate(
                alert_type="peak_usage",
                severity=peak["severity"],
                title=f"Peak consumption predicted: {peak['peak_kwh']:.1f} kWh",
                message=peak.get("alert_message", ""),
            ))
            created.append(a)

    return created
