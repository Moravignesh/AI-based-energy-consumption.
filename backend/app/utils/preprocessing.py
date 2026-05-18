"""
Preprocessing pipeline — cleans, validates, and engineers features
for any uploaded energy dataset.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Column alias map ──────────────────────────────────────────────────────────
_ALIASES: dict[str, str] = {
    "time": "timestamp", "date": "timestamp", "datetime": "timestamp",
    "ts": "timestamp", "date_time": "timestamp",
    "kwh": "energy_kwh", "energy": "energy_kwh", "consumption": "energy_kwh",
    "usage": "energy_kwh", "power_kwh": "energy_kwh", "power": "energy_kwh",
    "watt_hours": "energy_kwh", "wh": "energy_kwh",
    "device": "device_id", "sensor": "device_id", "meter": "device_id",
    "meter_id": "device_id", "sensor_id": "device_id",
    "building": "building_id", "location": "building_id", "site": "building_id",
    "temp": "temperature", "temp_c": "temperature", "outdoor_temp": "temperature",
    "hum": "humidity", "relative_humidity": "humidity",
    "people": "occupancy", "headcount": "occupancy",
}


def validate_and_clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Full preprocessing pipeline.
    Returns (cleaned_df, list_of_warnings).
    Raises ValueError for unrecoverable issues.
    """
    warnings: List[str] = []
    df = df.copy()

    # 1 ── Normalise column names ──────────────────────────────────────────
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    df.rename(columns={k: v for k, v in _ALIASES.items() if k in df.columns}, inplace=True)

    missing_required = {"timestamp", "energy_kwh"} - set(df.columns)
    if missing_required:
        raise ValueError(
            f"Missing required columns: {missing_required}. "
            f"Detected columns: {list(df.columns)}"
        )

    # 2 ── Timestamp parsing ───────────────────────────────────────────────
    df["timestamp"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True, errors="coerce")
    bad_ts = df["timestamp"].isna().sum()
    if bad_ts > 0:
        warnings.append(f"Dropped {bad_ts} rows with unparseable timestamps.")
        df = df.dropna(subset=["timestamp"])

    if df.empty:
        raise ValueError("No valid timestamps found in dataset.")

    # 3 ── Energy values ───────────────────────────────────────────────────
    df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
    bad_energy = df["energy_kwh"].isna().sum()
    if bad_energy > 0:
        warnings.append(f"Dropped {bad_energy} rows with non-numeric energy values.")
    df = df.dropna(subset=["energy_kwh"])
    df = df[df["energy_kwh"] >= 0]

    # Cap extreme outliers (>99.9th percentile × 5) but keep for anomaly detection
    p999 = df["energy_kwh"].quantile(0.999)
    hard_cap = p999 * 5
    capped = (df["energy_kwh"] > hard_cap).sum()
    if capped > 0:
        df["energy_kwh"] = df["energy_kwh"].clip(upper=hard_cap)
        warnings.append(f"Capped {capped} extreme energy values at {hard_cap:.2f} kWh.")

    # 4 ── Device / building IDs ───────────────────────────────────────────
    if "device_id" not in df.columns:
        df["device_id"] = "DEVICE-01"
        warnings.append("No 'device_id' column found — assigned 'DEVICE-01' to all records.")
    df["device_id"] = df["device_id"].fillna("UNKNOWN").astype(str).str.strip()

    if "building_id" not in df.columns:
        df["building_id"] = "Building-A"
    df["building_id"] = df["building_id"].fillna("Unknown").astype(str).str.strip()

    # 5 ── Optional numeric columns ────────────────────────────────────────
    for col in ["temperature", "humidity", "occupancy"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6 ── Sort & deduplicate ──────────────────────────────────────────────
    df = df.sort_values(["device_id", "timestamp"]).drop_duplicates(
        subset=["device_id", "timestamp"], keep="last"
    )

    # 7 ── Fill sparse hourly gaps per device ─────────────────────────────
    df = _fill_gaps(df, warnings)

    logger.info(
        f"Preprocessing done: {len(df):,} records | "
        f"{df['device_id'].nunique()} devices | {len(warnings)} warnings"
    )
    return df.reset_index(drop=True), warnings


def _fill_gaps(df: pd.DataFrame, warnings: List[str]) -> pd.DataFrame:
    """Interpolate missing hourly slots per device (max 6-hour gap)."""
    filled_parts = []
    for device, grp in df.groupby("device_id"):
        g = grp.set_index("timestamp").sort_index()
        full_idx = pd.date_range(g.index.min(), g.index.max(), freq="H")
        gaps = len(full_idx) - len(g)
        if gaps > 0:
            warnings.append(f"Device '{device}': filled {gaps} missing hourly slots via interpolation.")
        g = g.reindex(full_idx)
        g["energy_kwh"] = g["energy_kwh"].interpolate(method="time", limit=6)
        g["energy_kwh"] = g["energy_kwh"].fillna(g["energy_kwh"].median())
        g["device_id"]  = g["device_id"].fillna(device)
        g["building_id"] = g["building_id"].fillna(
            grp["building_id"].iloc[0] if len(grp) else "Unknown"
        )
        # Forward-fill optional columns
        for col in ["temperature", "humidity", "occupancy"]:
            if col in g.columns:
                g[col] = g[col].interpolate(method="time", limit=24).bfill().ffill()
        filled_parts.append(g.reset_index().rename(columns={"index": "timestamp"}))

    return pd.concat(filled_parts, ignore_index=True) if filled_parts else df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-series features needed by ML models."""
    df = df.copy().sort_values(["device_id", "timestamp"])

    df["hour"]            = df["timestamp"].dt.hour
    df["day_of_week"]     = df["timestamp"].dt.dayofweek
    df["day_of_year"]     = df["timestamp"].dt.dayofyear
    df["month"]           = df["timestamp"].dt.month
    df["quarter"]         = df["timestamp"].dt.quarter
    df["week_of_year"]    = df["timestamp"].dt.isocalendar().week.astype(int)
    df["is_weekend"]      = (df["day_of_week"] >= 5).astype(int)
    df["is_business_hour"]= ((df["hour"].between(8, 18)) & (df["is_weekend"] == 0)).astype(int)
    df["is_night"]        = ((df["hour"] < 6) | (df["hour"] > 22)).astype(int)

    # Cyclical encodings
    df["hour_sin"]   = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"]   = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"]    = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]    = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"]  = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"]  = np.cos(2 * np.pi * df["month"] / 12)

    # Lag features per device
    for lag in [1, 2, 3, 24, 48, 168]:
        df[f"lag_{lag}h"] = df.groupby("device_id")["energy_kwh"].shift(lag)

    # Rolling statistics
    for window in [6, 24, 168]:
        shifted = df.groupby("device_id")["energy_kwh"].shift(1)
        df[f"roll_{window}h_mean"] = shifted.groupby(df["device_id"]).transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
        df[f"roll_{window}h_std"] = shifted.groupby(df["device_id"]).transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0)
        )

    return df
