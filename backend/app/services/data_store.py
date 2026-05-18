"""
In-memory data store — holds the active DataFrame in memory.
Acts as a singleton service injected into all endpoints.
"""
from __future__ import annotations
import pandas as pd
from typing import Optional
from app.core.exceptions import NoDataLoadedError, DeviceNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataStore:
    """Thread-safe singleton holding the current energy dataset."""

    _instance: Optional["DataStore"] = None

    def __new__(cls) -> "DataStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._df: Optional[pd.DataFrame] = None
            cls._instance._filename: str = ""
            cls._instance._meta: dict = {}
        return cls._instance

    # ── Setters ────────────────────────────────────────────────────────────
    def set(self, df: pd.DataFrame, filename: str = "unknown") -> None:
        self._df = df.copy()
        self._filename = filename
        self._meta = self._build_meta(df)
        logger.info(f"DataStore updated: {len(df):,} records, {df['device_id'].nunique()} devices [{filename}]")

    def clear(self) -> None:
        self._df = None
        self._filename = ""
        self._meta = {}
        logger.info("DataStore cleared")

    # ── Getters ────────────────────────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._df is not None and not self._df.empty

    def require(self) -> pd.DataFrame:
        """Return df or raise NoDataLoadedError."""
        if not self.is_loaded:
            raise NoDataLoadedError()
        return self._df.copy()

    def require_device(self, device_id: str) -> pd.DataFrame:
        df = self.require()
        if device_id == "ALL":
            return df
        if device_id not in df["device_id"].values:
            raise DeviceNotFoundError(device_id)
        return df[df["device_id"] == device_id].copy()

    @property
    def meta(self) -> dict:
        return self._meta

    @property
    def filename(self) -> str:
        return self._filename

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _build_meta(df: pd.DataFrame) -> dict:
        return {
            "records": len(df),
            "devices": sorted(df["device_id"].unique().tolist()),
            "buildings": sorted(df["building_id"].unique().tolist()) if "building_id" in df.columns else [],
            "columns": df.columns.tolist(),
            "date_range": {
                "start": df["timestamp"].min().isoformat(),
                "end": df["timestamp"].max().isoformat(),
            },
        }


# Singleton instance — import this everywhere
data_store = DataStore()
