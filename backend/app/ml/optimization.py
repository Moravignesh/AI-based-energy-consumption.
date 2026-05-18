"""
Optimization Engine
────────────────────
Generates data-driven energy-saving recommendations from consumption patterns.
"""
from __future__ import annotations
import uuid
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
RATE = settings.ELECTRICITY_RATE_USD_KWH


# ── Analysis helpers ──────────────────────────────────────────────────────────

def _peak_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    hourly   = df.groupby(df["timestamp"].dt.hour)["energy_kwh"].mean()
    ph       = int(hourly.idxmax())
    oph      = int(hourly.idxmin())
    return {
        "peak_hour":      ph,
        "off_peak_hour":  oph,
        "peak_kwh":       round(float(hourly.max()), 4),
        "off_peak_kwh":   round(float(hourly.min()), 4),
        "load_factor":    round(float(hourly.min() / (hourly.max() + 1e-9)), 3),
        "peak_hours":     [int(h) for h in hourly.nlargest(4).index.tolist()],
        "off_peak_hours": [int(h) for h in hourly.nsmallest(6).index.tolist()],
    }


def _device_stats(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("device_id")
        .agg(total_kwh=("energy_kwh","sum"), mean_kwh=("energy_kwh","mean"),
             max_kwh=("energy_kwh","max"), std_kwh=("energy_kwh","std"))
        .reset_index().sort_values("total_kwh", ascending=False)
    )


def _night_ratio(df: pd.DataFrame) -> float:
    night = df[(df["timestamp"].dt.hour < 6) | (df["timestamp"].dt.hour >= 22)]
    return float(night["energy_kwh"].sum() / (df["energy_kwh"].sum() + 1e-9))


def _weekend_stats(df: pd.DataFrame) -> Dict[str, float]:
    df = df.copy()
    df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5
    g = df.groupby("is_weekend")["energy_kwh"].mean()
    wd = float(g.get(False, 0))
    we = float(g.get(True, 0))
    return {
        "weekday_avg": round(wd, 4),
        "weekend_avg": round(we, 4),
        "reduction_pct": round((wd - we) / (wd + 1e-9) * 100, 1),
    }


# ── Recommendation builders ───────────────────────────────────────────────────

def _rec(idx, category, priority, title, desc, savings_kwh, device_id=None):
    return {
        "id":    idx,
        "category": category,
        "priority": priority,
        "title":    title,
        "description": desc,
        "estimated_savings_kwh":      round(savings_kwh, 2),
        "estimated_cost_savings_usd": round(savings_kwh * RATE, 2),
        "roi_days": None,
        "device_id": device_id,
    }


def _build_recommendations(
    df: pd.DataFrame,
    peak: Dict, devs: pd.DataFrame,
    night_ratio: float, weekend: Dict,
    total_kwh: float, days: int,
) -> List[Dict]:
    recs, idx = [], 0

    # ① Load shifting
    if peak["load_factor"] < 0.60:
        savings = (peak["peak_kwh"] - peak["off_peak_kwh"]) * 4 * days * 0.30
        idx += 1
        recs.append(_rec(idx,"Load Balancing","high",
            f"Shift loads from peak ({peak['peak_hour']}:00) to off-peak ({peak['off_peak_hour']}:00)",
            f"Your load factor is {peak['load_factor']:.2f} (target ≥ 0.80). "
            f"Moving schedulable workloads — batch processing, EV charging, dishwashers — "
            f"away from {peak['peak_hour']}:00–{(peak['peak_hour']+2)%24}:00 reduces "
            f"peak demand charges and grid strain. Estimated 30 % of peak excess "
            f"is shiftable, saving ~{savings:.0f} kWh.",
            savings))

    # ② Night-time waste
    if night_ratio > 0.15:
        savings = total_kwh * night_ratio * 0.50
        idx += 1
        recs.append(_rec(idx,"Scheduling","high",
            "Reduce overnight energy consumption (10 PM – 6 AM)",
            f"{night_ratio*100:.1f}% of total energy is consumed overnight. "
            "Industry benchmark for commercial buildings is < 10 %. "
            "Implement automated shutdown schedules: "
            "HVAC setback to 18 °C/26 °C, non-essential lighting off, "
            "idle servers in low-power mode.",
            savings))

    # ③ Top consumer
    if not devs.empty:
        top = devs.iloc[0]
        savings = float(top["total_kwh"]) * 0.10
        idx += 1
        recs.append(_rec(idx,"Device Optimisation","medium",
            f"Optimise highest-consuming device: {top['device_id']}",
            f"{top['device_id']} accounts for "
            f"{top['total_kwh']/total_kwh*100:.1f}% of total usage "
            f"({top['total_kwh']:.0f} kWh). Consider: "
            "variable-speed drives, scheduled operating hours, "
            "or replacing with a higher-efficiency unit. "
            "A 10 % efficiency gain delivers the above saving.",
            savings, device_id=str(top["device_id"])))

    # ④ High-variance device (possible fault)
    if len(devs) > 1:
        hv = devs.nlargest(1, "std_kwh").iloc[0]
        if float(hv["std_kwh"]) > float(hv["mean_kwh"]) * 0.50:
            savings = float(hv["std_kwh"]) * days * 0.20
            idx += 1
            recs.append(_rec(idx,"Fault Detection","high",
                f"Investigate irregular consumption: {hv['device_id']}",
                f"{hv['device_id']} shows high variability "
                f"(σ = {hv['std_kwh']:.2f} kWh vs mean = {hv['mean_kwh']:.2f} kWh). "
                "This may indicate a failing component, refrigerant leak, "
                "or stuck actuator. A maintenance inspection is recommended.",
                savings, device_id=str(hv["device_id"])))

    # ⑤ Weekend idle
    if weekend["reduction_pct"] < 30:
        savings = weekend["weekday_avg"] * 0.15 * (days // 7) * 2 * 24
        idx += 1
        recs.append(_rec(idx,"Scheduling","medium",
            "Implement weekend energy-reduction schedule",
            f"Weekend consumption is only {weekend['reduction_pct']:.0f}% lower than weekday. "
            "Best-practice target is 40–60% for commercial buildings. "
            "Enable weekend setback mode: HVAC +/- 4 °C, "
            "corridor lighting at 30 %, and non-critical servers hibernating.",
            savings))

    # ⑥ HVAC
    hvac = devs[devs["device_id"].str.upper().str.contains("HVAC|AC|HEAT|COOL", na=False)]
    if not hvac.empty:
        hvac_kwh = float(hvac["total_kwh"].sum())
        idx += 1
        recs.append(_rec(idx,"HVAC","medium",
            "Optimise HVAC setpoints and enable demand-controlled ventilation",
            "Raising cooling setpoint by 2 °C during low occupancy cuts HVAC load 10–15 %. "
            "Enabling economiser mode during mild weather (10–18 °C) can reduce "
            "mechanical cooling by up to 40 %. "
            "Install CO₂ sensors for demand-controlled ventilation.",
            hvac_kwh * 0.12))

    # ⑦ Power factor / off-peak charging
    idx += 1
    recs.append(_rec(idx,"Sustainability","low",
        "Schedule battery/EV charging during off-peak hours",
        f"Charge battery storage or EVs during off-peak windows "
        f"({', '.join(str(h)+':00' for h in peak['off_peak_hours'][:3])}). "
        "This avoids peak tariffs and reduces grid demand charges. "
        "Pair with a smart energy management system (EMS) for automation.",
        total_kwh * 0.04))

    # ⑧ Lighting
    lighting = devs[devs["device_id"].str.upper().str.contains("LIGHT|LUM|LED", na=False)]
    if not lighting.empty:
        l_kwh = float(lighting["total_kwh"].sum())
        idx += 1
        recs.append(_rec(idx,"Lighting","low",
            "Upgrade to occupancy-sensor-controlled LED lighting",
            "Motion and daylight sensors can reduce lighting energy by 30–50 %. "
            "LED retrofits (if not already done) reduce consumption by 60 % vs fluorescent. "
            "Prioritise common areas, corridors, and car parks.",
            l_kwh * 0.35))

    recs.sort(key=lambda r: r["estimated_savings_kwh"], reverse=True)
    return recs


# ── Public API ────────────────────────────────────────────────────────────────

def run_optimization(df: pd.DataFrame, device_id: str = "ALL") -> Dict[str, Any]:
    if device_id != "ALL":
        df = df[df["device_id"] == device_id].copy()
    if len(df) < 24:
        raise ValueError("Need ≥ 24 records for optimization")

    total_kwh = float(df["energy_kwh"].sum())
    days      = max(1, (df["timestamp"].max() - df["timestamp"].min()).days)
    peak      = _peak_analysis(df)
    devs      = _device_stats(df)
    nr        = _night_ratio(df)
    weekend   = _weekend_stats(df)

    recs = _build_recommendations(df, peak, devs, nr, weekend, total_kwh, days)
    total_savings = sum(r["estimated_savings_kwh"] for r in recs)

    alerts = []
    if peak["load_factor"] < 0.50:
        alerts.append({
            "type": "peak", "severity": "high",
            "message": (f"Load factor is critically low ({peak['load_factor']:.2f}). "
                        f"Peak demand between {min(peak['peak_hours'])}:00–"
                        f"{max(peak['peak_hours'])+1}:00 needs immediate attention."),
        })
    elif peak["load_factor"] < 0.65:
        alerts.append({
            "type": "peak", "severity": "medium",
            "message": (f"Peak consumption expected at {peak['peak_hour']}:00. "
                        "Consider load-shifting non-critical equipment."),
        })

    return {
        "run_id":                       str(uuid.uuid4()),
        "recommendations":              recs,
        "peak_analysis":                peak,
        "device_summary":               devs.to_dict(orient="records"),
        "total_potential_savings_kwh":  round(total_savings, 2),
        "total_potential_savings_usd":  round(total_savings * RATE, 2),
        "savings_potential_pct":        round(total_savings / (total_kwh + 1e-9) * 100, 1),
        "alerts":                       alerts,
        "created_at":                   datetime.utcnow().isoformat(),
    }
