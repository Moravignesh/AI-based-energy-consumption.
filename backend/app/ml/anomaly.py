"""
Anomaly Detection ML module
────────────────────────────
Methods  : Isolation Forest, Z-Score, Ensemble (both)
Classifies anomalies into 5 types: spike, drop, night_spike,
extreme_deviation, statistical_anomaly
"""
from __future__ import annotations
import uuid
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger(__name__)

_ANOMALY_TYPES = {
    "consumption_spike":  "Consumption Spike",
    "sudden_drop":        "Sudden Drop",
    "night_spike":        "Night-time Spike",
    "extreme_deviation":  "Extreme Deviation",
    "statistical_anomaly":"Statistical Anomaly",
}


# ── Feature engineering ───────────────────────────────────────────────────────

def _build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    df = df.copy().sort_values("timestamp")
    df["hour"]       = df["timestamp"].dt.hour
    df["dow"]        = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(float)
    df["is_night"]   = ((df["hour"] < 6) | (df["hour"] > 22)).astype(float)

    grp = df.groupby("device_id")["energy_kwh"]
    df["roll_mean_24"] = grp.transform(lambda x: x.rolling(24, min_periods=4).mean().shift(1))
    df["roll_std_24"]  = grp.transform(lambda x: x.rolling(24, min_periods=4).std().shift(1).fillna(0))
    df["roll_mean_168"]= grp.transform(lambda x: x.rolling(168, min_periods=24).mean().shift(1))
    df["zscore"]       = (df["energy_kwh"] - df["roll_mean_24"]) / (df["roll_std_24"] + 1e-6)
    df["dev_ratio"]    = df["energy_kwh"] / (df["roll_mean_24"] + 1e-6)

    feature_cols = [
        "energy_kwh", "hour", "dow", "is_weekend", "is_night",
        "zscore", "dev_ratio",
    ]
    return df, feature_cols


def _classify(row: pd.Series) -> str:
    h     = row.get("hour", 12)
    kwh   = row.get("energy_kwh", 0)
    mean  = row.get("roll_mean_24", kwh)
    ratio = row.get("dev_ratio", 1.0)
    z     = abs(row.get("zscore", 0))

    if h < 6 and kwh > mean * 1.5:
        return "night_spike"
    if ratio > 2.5:
        return "consumption_spike"
    if ratio < 0.2:
        return "sudden_drop"
    if z > 4:
        return "extreme_deviation"
    return "statistical_anomaly"


# ── Detection methods ─────────────────────────────────────────────────────────

def _isolation_forest(df: pd.DataFrame, feature_cols: List[str], contamination: float) -> pd.DataFrame:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    clean = df.dropna(subset=feature_cols).copy()
    sc    = StandardScaler()
    X     = sc.fit_transform(clean[feature_cols])

    clf = IsolationForest(
        n_estimators=200, contamination=contamination,
        random_state=42, n_jobs=-1,
    )
    clf.fit(X)
    scores = clf.decision_function(X)
    preds  = clf.predict(X)

    clean["_if_score"]   = -scores          # higher = more anomalous
    clean["_if_anomaly"] = (preds == -1)

    df = df.merge(
        clean[["_if_score", "_if_anomaly"]],
        left_index=True, right_index=True, how="left",
    )
    df["_if_score"]   = df["_if_score"].fillna(0)
    df["_if_anomaly"] = df["_if_anomaly"].fillna(False)
    return df


def _zscore_detect(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    df["_z_anomaly"] = df["zscore"].abs() > threshold
    df["_z_score"]   = df["zscore"].abs() / threshold
    return df


# ── Public API ────────────────────────────────────────────────────────────────

def run_anomaly_detection(
    df: pd.DataFrame,
    device_id: str = "ALL",
    method: str = "ensemble",
    sensitivity: float = 0.05,
) -> Dict[str, Any]:

    if device_id != "ALL":
        df = df[df["device_id"] == device_id].copy()

    if len(df) < 48:
        raise ValueError(f"Need ≥ 48 records, got {len(df)}")

    contamination = float(np.clip(sensitivity, 0.01, 0.30))
    df, feature_cols = _build_features(df)

    if method == "isolation_forest":
        df = _isolation_forest(df, feature_cols, contamination)
        df["is_anomaly"]    = df["_if_anomaly"]
        df["anomaly_score"] = df["_if_score"]

    elif method == "zscore":
        df = _zscore_detect(df, threshold=3.0)
        df["is_anomaly"]    = df["_z_anomaly"]
        df["anomaly_score"] = df["_z_score"].fillna(0)

    else:  # ensemble
        df = _isolation_forest(df, feature_cols, contamination)
        df = _zscore_detect(df, threshold=3.0)
        df["is_anomaly"]    = df["_if_anomaly"] | df["_z_anomaly"].fillna(False)
        df["anomaly_score"] = (
            (df["_if_score"].fillna(0) + df["_z_score"].fillna(0)) / 2
        )

    mask = df["is_anomaly"].fillna(False)
    df.loc[mask, "anomaly_type"] = df[mask].apply(_classify, axis=1)

    # ── Build response ────────────────────────────────────────────────────
    anomaly_df = df[mask].copy()

    anomalies = [
        {
            "timestamp":     row["timestamp"].strftime("%Y-%m-%dT%H:%M:%S"),
            "device_id":     str(row.get("device_id", "UNKNOWN")),
            "energy_kwh":    round(float(row["energy_kwh"]), 4),
            "anomaly_score": round(float(row.get("anomaly_score", 0)), 4),
            "anomaly_type":  str(row.get("anomaly_type", "unknown")),
            "is_anomaly":    True,
        }
        for _, row in anomaly_df.iterrows()
    ]

    # Sub-sample time series to ≤ 800 points for the chart
    display = df.copy()
    if len(display) > 800:
        display = display.iloc[::len(display) // 800]

    time_series = [
        {
            "timestamp":     row["timestamp"].strftime("%Y-%m-%dT%H:%M:%S"),
            "device_id":     str(row.get("device_id", "UNKNOWN")),
            "energy_kwh":    round(float(row["energy_kwh"]), 4),
            "is_anomaly":    bool(row.get("is_anomaly", False)),
            "anomaly_score": round(float(row.get("anomaly_score", 0)), 4),
        }
        for _, row in display.iterrows()
    ]

    device_summary = (
        df.groupby("device_id")
        .agg(total_readings=("energy_kwh","count"), anomaly_count=("is_anomaly","sum"))
        .reset_index()
    )
    device_summary["anomaly_rate_pct"] = (
        device_summary["anomaly_count"] / device_summary["total_readings"] * 100
    ).round(2)

    return {
        "run_id":           str(uuid.uuid4()),
        "method":           method,
        "device_id":        device_id,
        "total_records":    int(len(df)),
        "anomaly_count":    int(mask.sum()),
        "anomaly_rate_pct": round(float(mask.mean() * 100), 2),
        "anomalies":        anomalies,
        "time_series":      time_series,
        "device_summary":   device_summary.to_dict(orient="records"),
        "anomaly_types":    (
            anomaly_df["anomaly_type"].value_counts().to_dict()
            if not anomaly_df.empty else {}
        ),
        "created_at":       datetime.utcnow().isoformat(),
    }
