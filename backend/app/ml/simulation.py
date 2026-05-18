"""
Scenario Simulation Engine
───────────────────────────
Scenarios: occupancy_change | temperature_change | device_shutdown | peak_reduction
Uses last 7 days as baseline; returns hourly comparison + annualised projections.
"""
from __future__ import annotations
import uuid
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import settings
from app.core.exceptions import InvalidScenarioError
from app.core.logging import get_logger

logger = get_logger(__name__)
RATE = settings.ELECTRICITY_RATE_USD_KWH


# ── Scenario functions ────────────────────────────────────────────────────────

def _occupancy_change(arr: np.ndarray, p: Dict) -> tuple[np.ndarray, List[str]]:
    new_occ  = float(p.get("occupancy_pct", 50))
    base_occ = float(p.get("baseline_occupancy_pct", 80))
    sens     = float(np.clip(p.get("sensitivity", 0.60), 0.1, 1.0))

    ratio    = new_occ / (base_occ + 1e-9)
    base_frac = 0.30
    scale    = base_frac + (1 - base_frac) * (1 - sens * (1 - ratio))
    scale    = float(np.clip(scale, 0.10, 2.0))

    return arr * scale, [
        f"Occupancy changed from {base_occ:.0f}% to {new_occ:.0f}%.",
        f"HVAC and lighting loads scale with occupancy (sensitivity={sens}).",
        "Base loads (servers, security, lifts) remain at 30% constant.",
        f"Effective load scale factor: {scale:.3f}",
    ]


def _temperature_change(arr: np.ndarray, p: Dict) -> tuple[np.ndarray, List[str]]:
    delta     = float(p.get("temp_delta_c", 5.0))
    hvac_frac = float(np.clip(p.get("hvac_fraction", 0.40), 0.05, 0.85))

    # ~3 % HVAC load per °C for commercial buildings
    scale = 1.0 + hvac_frac * delta * 0.03
    scale = float(np.clip(scale, 0.40, 2.50))

    return arr * scale, [
        f"Outdoor temperature change: {'+' if delta >= 0 else ''}{delta:.1f} °C.",
        f"HVAC fraction of load: {hvac_frac*100:.0f}%.",
        "HVAC load adjusts at ~3%/°C (ASHRAE commercial benchmark).",
        f"Effective load scale factor: {scale:.3f}",
    ]


def _device_shutdown(arr: np.ndarray, p: Dict) -> tuple[np.ndarray, List[str]]:
    dev_load   = float(p.get("device_kwh_per_hour", 2.0))
    start_hr   = int(p.get("shutdown_start_hour", 22))
    end_hr     = int(p.get("shutdown_end_hour", 6))

    result = arr.copy()
    for i in range(len(result)):
        h = i % 24
        if start_hr <= h or h < end_hr:
            result[i] = max(0.0, result[i] - dev_load)

    total_saved = float(arr.sum() - result.sum())
    return result, [
        f"Device load removed: {dev_load:.1f} kWh/hour during shutdown window.",
        f"Shutdown window: {start_hr}:00 – {end_hr}:00 daily.",
        f"Total energy removed over period: {total_saved:.1f} kWh.",
        "Other loads remain unchanged.",
    ]


def _peak_reduction(arr: np.ndarray, p: Dict) -> tuple[np.ndarray, List[str]]:
    red_pct   = float(np.clip(p.get("reduction_pct", 20), 1, 80)) / 100
    threshold = float(np.clip(p.get("peak_threshold_pct", 20), 5, 50)) / 100

    thresh_val = np.quantile(arr, 1 - threshold)
    result     = arr.copy()
    mask       = result > thresh_val
    result[mask] = result[mask] * (1 - red_pct)

    peak_hrs = int(mask.sum())
    return result, [
        f"Peak load cut by {red_pct*100:.0f}% on top {threshold*100:.0f}% of hours.",
        f"Peak threshold: {thresh_val:.2f} kWh/hour ({peak_hrs} affected hours).",
        "Achieved via demand-response, battery discharge, or load shedding.",
        "Reduces both energy cost and demand charges.",
    ]


_SCENARIOS: Dict[str, callable] = {
    "occupancy_change":  _occupancy_change,
    "temperature_change": _temperature_change,
    "device_shutdown":   _device_shutdown,
    "peak_reduction":    _peak_reduction,
}

SCENARIO_META = {
    "occupancy_change": {
        "label": "Occupancy Change",
        "description": "Model energy impact of changing building occupancy levels.",
        "parameters": [
            {"key":"occupancy_pct","label":"New Occupancy (%)","type":"number","default":50,"min":0,"max":100},
            {"key":"baseline_occupancy_pct","label":"Baseline Occupancy (%)","type":"number","default":80,"min":10,"max":100},
            {"key":"sensitivity","label":"HVAC/Lighting Sensitivity","type":"number","default":0.6,"min":0.1,"max":1.0},
        ],
    },
    "temperature_change": {
        "label": "Temperature Change",
        "description": "Simulate HVAC load shift from outdoor temperature change.",
        "parameters": [
            {"key":"temp_delta_c","label":"Temperature Change (°C)","type":"number","default":5,"min":-15,"max":15},
            {"key":"hvac_fraction","label":"HVAC Fraction of Load","type":"number","default":0.40,"min":0.05,"max":0.85},
        ],
    },
    "device_shutdown": {
        "label": "Device Shutdown",
        "description": "Simulate scheduled device shutdown during off-hours.",
        "parameters": [
            {"key":"device_kwh_per_hour","label":"Device Load (kWh/hr)","type":"number","default":2.0,"min":0.1,"max":50},
            {"key":"shutdown_start_hour","label":"Shutdown Start Hour","type":"number","default":22,"min":0,"max":23},
            {"key":"shutdown_end_hour","label":"Shutdown End Hour","type":"number","default":6,"min":0,"max":12},
        ],
    },
    "peak_reduction": {
        "label": "Peak Load Reduction",
        "description": "Simulate demand-response / peak-shaving strategy.",
        "parameters": [
            {"key":"reduction_pct","label":"Peak Reduction (%)","type":"number","default":20,"min":5,"max":60},
            {"key":"peak_threshold_pct","label":"Define Peak as Top (%)","type":"number","default":20,"min":5,"max":40},
        ],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def run_simulation(
    df: pd.DataFrame,
    scenario: str,
    params: Dict[str, Any],
    device_id: str = "ALL",
) -> Dict[str, Any]:

    if scenario not in _SCENARIOS:
        raise InvalidScenarioError(scenario)

    if device_id != "ALL":
        df = df[df["device_id"] == device_id].copy()

    if len(df) < 24:
        raise ValueError("Need ≥ 24 records for simulation")

    # Build 7-day hourly baseline
    cutoff  = df["timestamp"].max() - pd.Timedelta(days=7)
    recent  = df[df["timestamp"] >= cutoff].copy()
    series  = (recent.set_index("timestamp")["energy_kwh"]
                     .resample("H").mean().interpolate("time"))
    baseline_arr = series.values.copy()

    fn = _SCENARIOS[scenario]
    simulated_arr, insights = fn(baseline_arr, params)

    base_total = float(baseline_arr.sum())
    sim_total  = float(simulated_arr.sum())
    savings    = base_total - sim_total
    pct        = savings / (base_total + 1e-9) * 100
    cost_saved = savings * RATE

    # Hourly profile (cap at 1 week)
    ts_idx = series.index
    profile = [
        {
            "timestamp":    ts_idx[i].strftime("%Y-%m-%dT%H:%M:%S") if i < len(ts_idx) else f"H+{i}",
            "baseline_kwh": round(float(baseline_arr[i]), 4),
            "simulated_kwh":round(float(simulated_arr[i]), 4),
            "savings_kwh":  round(float(baseline_arr[i] - simulated_arr[i]), 4),
        }
        for i in range(min(len(baseline_arr), 168))
    ]

    meta = SCENARIO_META.get(scenario, {})

    return {
        "run_id":                str(uuid.uuid4()),
        "scenario":              meta.get("label", scenario),
        "scenario_key":          scenario,
        "parameters":            params,
        "device_id":             device_id,
        "baseline_kwh":          round(base_total, 2),
        "simulated_kwh":         round(sim_total, 2),
        "energy_savings_kwh":    round(savings, 2),
        "cost_savings_usd":      round(cost_saved, 2),
        "savings_percent":       round(pct, 1),
        "annualized_savings_kwh":round(savings / 7 * 365, 0),
        "annualized_savings_usd":round(cost_saved / 7 * 365, 2),
        "hourly_profile":        profile,
        "insights":              insights,
        "created_at":            datetime.utcnow().isoformat(),
    }
