from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    DateTime, Boolean, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class EnergyReading(Base):
    __tablename__ = "energy_readings"
    id            = Column(Integer, primary_key=True, index=True)
    timestamp     = Column(DateTime, nullable=False)
    device_id     = Column(String(100), nullable=False)
    building_id   = Column(String(100), nullable=True)
    energy_kwh    = Column(Float, nullable=False)
    temperature   = Column(Float, nullable=True)
    humidity      = Column(Float, nullable=True)
    occupancy     = Column(Integer, nullable=True)
    is_anomaly    = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    anomaly_type  = Column(String(60), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index("ix_er_device_ts", "device_id", "timestamp"),
    )


class ForecastResult(Base):
    __tablename__ = "forecast_results"
    id            = Column(Integer, primary_key=True, index=True)
    run_id        = Column(String(36), nullable=False, index=True)
    device_id     = Column(String(100), nullable=False)
    horizon       = Column(String(10))
    model_used    = Column(String(50))
    timestamp     = Column(DateTime)
    predicted_kwh = Column(Float)
    lower_bound   = Column(Float, nullable=True)
    upper_bound   = Column(Float, nullable=True)
    mae           = Column(Float, nullable=True)
    rmse          = Column(Float, nullable=True)
    accuracy_pct  = Column(Float, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"
    id            = Column(Integer, primary_key=True, index=True)
    run_id        = Column(String(36), nullable=False, index=True)
    timestamp     = Column(DateTime, nullable=False)
    device_id     = Column(String(100), nullable=False)
    energy_kwh    = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    anomaly_type  = Column(String(60), nullable=True)
    method        = Column(String(30), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id            = Column(Integer, primary_key=True, index=True)
    alert_type    = Column(String(60))
    severity      = Column(String(20))    # low | medium | high | critical
    title         = Column(String(200))
    message       = Column(Text)
    device_id     = Column(String(100), nullable=True)
    building_id   = Column(String(100), nullable=True)
    is_read       = Column(Boolean, default=False)
    is_resolved   = Column(Boolean, default=False)
    resolved_at   = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"
    id                     = Column(Integer, primary_key=True, index=True)
    run_id                 = Column(String(36), nullable=False, index=True)
    device_id              = Column(String(100), nullable=True)
    total_savings_kwh      = Column(Float)
    total_savings_usd      = Column(Float)
    savings_potential_pct  = Column(Float)
    rec_count              = Column(Integer)
    created_at             = Column(DateTime, default=datetime.utcnow)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id                  = Column(Integer, primary_key=True, index=True)
    run_id              = Column(String(36), nullable=False, index=True)
    scenario            = Column(String(80))
    parameters          = Column(Text)
    baseline_kwh        = Column(Float)
    simulated_kwh       = Column(Float)
    energy_savings_kwh  = Column(Float)
    cost_savings_usd    = Column(Float)
    savings_percent     = Column(Float)
    created_at          = Column(DateTime, default=datetime.utcnow)


class ModelAccuracy(Base):
    __tablename__ = "model_accuracy"
    id           = Column(Integer, primary_key=True, index=True)
    model_name   = Column(String(60))
    device_id    = Column(String(100))
    horizon      = Column(String(10))
    mae          = Column(Float)
    rmse         = Column(Float)
    mape         = Column(Float)
    accuracy_pct = Column(Float)
    data_points  = Column(Integer)
    created_at   = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
