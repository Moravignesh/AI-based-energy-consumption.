"""
Forecasting ML module
─────────────────────
Models   : ARIMA (statsmodels), Ridge Regression (sklearn)
Horizons : 24 h, 7 d, 30 d
Output   : predictions + 95 % confidence intervals + peak alerts
"""
from __future__ import annotations
import uuid, time, warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from app.core.logging import get_logger

warnings.filterwarnings("ignore")
logger = get_logger(__name__)

HORIZON_HOURS = {"24h": 24, "7d": 168, "30d": 720}
ELECTRICITY_RATE = 0.12


# ── Helpers ───────────────────────────────────────────────────────────────────

def _metrics(actual: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    mae  = float(np.mean(np.abs(actual - pred)))
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
    mape = float(np.mean(np.abs((actual - pred) / (np.abs(actual) + 1e-6))) * 100)
    return {
        "mae":          round(mae, 4),
        "rmse":         round(rmse, 4),
        "accuracy_pct": round(max(0.0, 100 - mape), 2),
    }


def _time_features(timestamps: pd.DatetimeIndex) -> np.ndarray:
    h   = timestamps.hour
    dow = timestamps.dayofweek
    mo  = timestamps.month
    return np.column_stack([
        np.sin(2 * np.pi * h / 24),   np.cos(2 * np.pi * h / 24),
        np.sin(2 * np.pi * dow / 7),  np.cos(2 * np.pi * dow / 7),
        np.sin(2 * np.pi * mo / 12),  np.cos(2 * np.pi * mo / 12),
        (dow >= 5).astype(float),
        ((h >= 8) & (h <= 18) & (dow < 5)).astype(float),
        ((h < 6) | (h > 22)).astype(float),
    ])


# ── Model implementations ─────────────────────────────────────────────────────

def _ridge(series: pd.Series, n_hours: int) -> Dict[str, Any]:
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    future_idx = pd.date_range(series.index[-1] + timedelta(hours=1), periods=n_hours, freq="H")
    X_hist  = _time_features(series.index)
    X_fut   = _time_features(future_idx)
    y       = series.values

    sc = StandardScaler()
    X_hist_s = sc.fit_transform(X_hist)
    X_fut_s  = sc.transform(X_fut)

    n_train = min(len(y), 60 * 24)
    model   = Ridge(alpha=1.0)
    model.fit(X_hist_s[-n_train:], y[-n_train:])

    pred = np.clip(model.predict(X_fut_s), 0, None)
    resid_std = float(np.std(y[-n_train:] - model.predict(X_hist_s[-n_train:])))
    val_mets = _metrics(y[-min(24, len(y)):], model.predict(X_hist_s[-min(24, len(y)):]))

    return {"model": "LinearRegression", "future_idx": future_idx,
            "pred": pred, "std": resid_std, **val_mets}


def _arima(series: pd.Series, n_hours: int) -> Dict[str, Any]:
    try:
        from statsmodels.tsa.arima.model import ARIMA

        daily  = series.resample("D").sum()
        n_days = max(1, n_hours // 24)
        fit    = ARIMA(daily.values[-min(90, len(daily)):], order=(2, 1, 2)).fit()
        fc     = fit.forecast(steps=n_days)
        ci     = fit.get_forecast(steps=n_days).conf_int()

        hw = _HOUR_PROFILE_WEIGHTS()
        future_idx = pd.date_range(series.index[-1] + timedelta(hours=1), periods=n_hours, freq="H")
        pred, lo, hi = [], [], []
        for i in range(n_hours):
            d  = min(i // 24, n_days - 1)
            w  = hw[i % 24]
            pred.append(max(0, fc[d] / 24 * w))
            lo.append(max(0, ci.iloc[d, 0] / 24 * w))
            hi.append(max(0, ci.iloc[d, 1] / 24 * w))

        pred_arr = np.array(pred)
        in_sample = fit.fittedvalues
        actual_d  = daily.values[-len(in_sample):]
        val_mets  = _metrics(actual_d, in_sample)

        return {"model": "ARIMA", "future_idx": future_idx,
                "pred": pred_arr, "lo": np.array(lo), "hi": np.array(hi), **val_mets}

    except Exception as e:
        logger.warning(f"ARIMA failed ({e}), falling back to Ridge")
        return _ridge(series, n_hours)


def _HOUR_PROFILE_WEIGHTS() -> np.ndarray:
    w = np.array([
        0.28,0.25,0.22,0.20,0.22,0.30,0.55,0.80,0.95,1.00,
        0.98,0.97,0.96,0.97,0.98,0.99,0.97,0.90,0.82,0.78,
        0.72,0.65,0.52,0.38,
    ])
    return w / w.sum() * 24


# ── Peak detection ────────────────────────────────────────────────────────────

def _detect_peaks(pred: np.ndarray, idx: pd.DatetimeIndex) -> List[Dict]:
    if len(pred) == 0:
        return []
    mu, sigma = pred.mean(), pred.std()
    thresh = mu + 1.5 * sigma
    peaks, i = [], 0
    while i < len(pred):
        if pred[i] > thresh:
            s = i
            while i < len(pred) and pred[i] > thresh:
                i += 1
            e = i - 1
            pk = float(pred[s:e+1].max())
            severity = "high" if pk > mu + 2.5 * sigma else "medium"
            peaks.append({
                "start": idx[s].strftime("%Y-%m-%dT%H:%M:%S"),
                "end":   idx[e].strftime("%Y-%m-%dT%H:%M:%S"),
                "peak_kwh": round(pk, 3),
                "severity": severity,
                "alert_message": (
                    f"Expected peak of {pk:.2f} kWh between "
                    f"{idx[s].strftime('%I %p')} – {idx[e].strftime('%I %p')}"
                ),
            })
        else:
            i += 1
    return peaks


# ── Public API ────────────────────────────────────────────────────────────────

def run_forecast(
    df: pd.DataFrame,
    device_id: str = "ALL",
    horizon: str = "24h",
    model: str = "auto",
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    n_hours = HORIZON_HOURS.get(horizon, 24)

    # Aggregate
    if device_id == "ALL":
        series = df.groupby("timestamp")["energy_kwh"].sum().sort_index()
    else:
        series = (df[df["device_id"] == device_id]
                    .set_index("timestamp")["energy_kwh"].sort_index())

    series = series.resample("H").mean().interpolate("time")

    if len(series) < 48:
        raise ValueError(f"Need ≥ 48 hourly records, got {len(series)}")

    # Select & run model
    if model == "linear":
        res = _ridge(series, n_hours)
    elif model == "arima":
        res = _arima(series, n_hours)
    else:   # auto
        res = _arima(series, n_hours)

    pred = res["pred"]
    std  = res.get("std", float(np.std(pred) * 0.1))
    lo   = res.get("lo", np.clip(pred - 1.96 * std, 0, None))
    hi   = res.get("hi", pred + 1.96 * std)

    points = [
        {
            "timestamp":     ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "predicted_kwh": round(float(p), 4),
            "lower_bound":   round(float(l), 4),
            "upper_bound":   round(float(u), 4),
        }
        for ts, p, l, u in zip(res["future_idx"], pred, lo, hi)
    ]

    elapsed = int((time.perf_counter() - t0) * 1000)
    run_id  = str(uuid.uuid4())

    return {
        "run_id":               run_id,
        "device_id":            device_id,
        "horizon":              horizon,
        "model_used":           res["model"],
        "total_predicted_kwh":  round(float(pred.sum()), 2),
        "forecast":             points,
        "peak_predictions":     _detect_peaks(pred, res["future_idx"]),
        "mae":                  res.get("mae"),
        "rmse":                 res.get("rmse"),
        "accuracy_pct":         res.get("accuracy_pct"),
        "training_time_ms":     elapsed,
        "created_at":           datetime.utcnow().isoformat(),
    }


def compare_models(
    df: pd.DataFrame,
    device_id: str = "ALL",
    horizon: str = "24h",
) -> Dict[str, Any]:
    """Run all models and return a side-by-side comparison."""
    results = []
    for m in ["linear", "arima"]:
        t0 = time.perf_counter()
        try:
            r = run_forecast(df, device_id=device_id, horizon=horizon, model=m)
            results.append({
                "model_name":      r["model_used"],
                "mae":             r.get("mae") or 0,
                "rmse":            r.get("rmse") or 0,
                "accuracy_pct":    r.get("accuracy_pct") or 0,
                "training_time_ms": int((time.perf_counter() - t0) * 1000),
                "forecast_points": r["forecast"][:24],
            })
        except Exception as e:
            logger.warning(f"Model '{m}' failed: {e}")

    best = max(results, key=lambda x: x["accuracy_pct"], default={})
    return {
        "device_id":     device_id,
        "horizon":       horizon,
        "results":       results,
        "best_model":    best.get("model_name", "N/A"),
        "comparison_at": datetime.utcnow().isoformat(),
    }
