"""
Application configuration — reads from .env or environment variables.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────
    APP_NAME: str = "Energy AI Platform"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── API ───────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./energy_platform.db"

    # ── ML ────────────────────────────────────────────────
    ELECTRICITY_RATE_USD_KWH: float = 0.12
    MAX_FORECAST_DAYS: int = 30
    ANOMALY_CONTAMINATION: float = 0.05

    # ── Pagination ────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
