"""Basic unit tests for ML modules."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd, numpy as np, pytest
from datetime import datetime, timedelta

def _make_df(n=200):
    idx = pd.date_range("2024-01-01", periods=n, freq="H")
    return pd.DataFrame({
        "timestamp": idx, "device_id": "TEST-01",
        "building_id": "Bldg-A",
        "energy_kwh": 3.0 + np.sin(np.arange(n) * 2*np.pi/24) + np.random.normal(0,.2,n),
    })

def test_preprocessing():
    from app.utils.preprocessing import validate_and_clean
    df, w = validate_and_clean(_make_df())
    assert len(df) >= 100
    assert "energy_kwh" in df.columns
    assert "device_id"  in df.columns

def test_forecasting():
    from app.ml.forecasting import run_forecast
    df = _make_df(300)
    df, _ = __import__("app.utils.preprocessing",fromlist=["validate_and_clean"]).validate_and_clean(df)
    r = run_forecast(df, horizon="24h", model="linear")
    assert len(r["forecast"]) == 24
    assert r["total_predicted_kwh"] > 0

def test_anomaly():
    from app.ml.anomaly import run_anomaly_detection
    df = _make_df(300)
    df, _ = __import__("app.utils.preprocessing",fromlist=["validate_and_clean"]).validate_and_clean(df)
    r = run_anomaly_detection(df, method="zscore")
    assert "anomaly_count" in r
    assert "time_series"   in r

def test_optimization():
    from app.ml.optimization import run_optimization
    df = _make_df(300)
    df, _ = __import__("app.utils.preprocessing",fromlist=["validate_and_clean"]).validate_and_clean(df)
    r = run_optimization(df)
    assert len(r["recommendations"]) > 0
    assert r["total_potential_savings_kwh"] >= 0

def test_simulation():
    from app.ml.simulation import run_simulation
    df = _make_df(300)
    df, _ = __import__("app.utils.preprocessing",fromlist=["validate_and_clean"]).validate_and_clean(df)
    r = run_simulation(df, "peak_reduction", {"reduction_pct":20,"peak_threshold_pct":20})
    assert "savings_percent" in r
    assert len(r["hourly_profile"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
