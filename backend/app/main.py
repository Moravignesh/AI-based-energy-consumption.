"""
⚡ Energy AI Platform v2 — FastAPI Application
================================================
Run locally:
    cd backend
    uvicorn app.main:app --reload --port 8000

API docs: http://localhost:8000/docs
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    EnergyPlatformError, energy_platform_exception_handler,
    generic_exception_handler,
)
from app.database import init_db
from app.api.v1.router import api_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    init_db()
    logger.info("Database initialised ✓")
    yield
    logger.info("Shutting down gracefully.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"⚡ {settings.APP_NAME}",
    description=(
        "AI-powered platform for energy consumption **forecasting**, "
        "**anomaly detection**, **optimization** and **scenario simulation**.\n\n"
        "Upload your CSV or generate sample data, then explore all endpoints."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timer(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t0) * 1000
    response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
    return response


# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(EnergyPlatformError, energy_platform_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"], include_in_schema=False)
def root():
    return {
        "service":     settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "status":      "running",
        "docs":        "/docs",
        "redoc":       "/redoc",
        "health":      f"{settings.API_V1_PREFIX}/health/",
        "api_prefix":  settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Root"])
def root_health():
    """Quick health probe — used by Docker / load balancers."""
    return {"status": "ok"}
