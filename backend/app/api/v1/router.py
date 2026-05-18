from fastapi import APIRouter
from app.api.v1.endpoints import (
    upload, dashboard, forecast, anomaly,
    optimization, simulation, alerts, devices,
    reports, models_compare, health,
)

api_router = APIRouter()

api_router.include_router(upload.router,          prefix="/upload",       tags=["📁 Upload"])
api_router.include_router(dashboard.router,       prefix="/dashboard",    tags=["📊 Dashboard"])
api_router.include_router(forecast.router,        prefix="/forecast",     tags=["📈 Forecast"])
api_router.include_router(anomaly.router,         prefix="/anomaly",      tags=["🔍 Anomaly"])
api_router.include_router(optimization.router,    prefix="/optimization", tags=["💡 Optimization"])
api_router.include_router(simulation.router,      prefix="/simulation",   tags=["🔬 Simulation"])
api_router.include_router(alerts.router,          prefix="/alerts",       tags=["🔔 Alerts"])
api_router.include_router(devices.router,         prefix="/devices",      tags=["🖥️  Devices"])
api_router.include_router(reports.router,         prefix="/reports",      tags=["📄 Reports"])
api_router.include_router(models_compare.router,  prefix="/models",       tags=["🤖 Models"])
api_router.include_router(health.router,          prefix="/health",       tags=["❤️  Health"])
