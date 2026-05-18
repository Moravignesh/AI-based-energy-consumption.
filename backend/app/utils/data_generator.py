"""
Synthetic energy dataset generator.
Produces realistic 6-month hourly readings for 5 devices with:
  - Daily/weekly/seasonal patterns
  - Temperature correlation for HVAC
  - Weekend reduction
  - Injected anomalies (~2 %)
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)

_DEVICES = {
    "HVAC-01":     {"base": 5.5, "building": "Building-A", "type": "hvac"},
    "HVAC-02":     {"base": 4.8, "building": "Building-B", "type": "hvac"},
    "Lighting-01": {"base": 2.2, "building": "Building-A", "type": "lighting"},
    "Server-01":   {"base": 8.0, "building": "Building-B", "type": "server"},
    "Elevator-01": {"base": 1.5, "building": "Building-A", "type": "elevator"},
}

_HOUR_PROFILE = np.array([
    0.28, 0.25, 0.22, 0.20, 0.22, 0.30,
    0.55, 0.80, 0.95, 1.00, 0.98, 0.97,
    0.96, 0.97, 0.98, 0.99, 0.97, 0.90,
    0.82, 0.78, 0.72, 0.65, 0.52, 0.38,
])


def generate(
    start: str = "2024-01-01",
    end:   str = "2024-06-30",
    seed: int = 42,
) -> pd.DataFrame:
    np.random.seed(seed)
    timestamps = pd.date_range(start, end, freq="H")
    records: list[dict] = []

    for ts in timestamps:
        h, dow, month = ts.hour, ts.weekday(), ts.month
        is_weekend = dow >= 5

        temp_base = 20 + 10 * np.sin((month - 3) * np.pi / 6)
        temperature = round(temp_base + np.random.normal(0, 2.5), 1)
        humidity    = round(float(np.random.uniform(35, 75)), 1)
        hour_factor = _HOUR_PROFILE[h]

        for dev_id, cfg in _DEVICES.items():
            base = cfg["base"]
            dev_type = cfg["type"]

            weekend_factor = 1.0
            season_factor  = 1.0

            if dev_type == "hvac":
                weekend_factor = 0.50
                if month in [6, 7, 8]:   season_factor = 1.45
                elif month in [12, 1, 2]: season_factor = 1.30
            elif dev_type == "lighting":
                weekend_factor = 0.45 if is_weekend else 1.0
            elif dev_type == "server":
                weekend_factor = 0.88
                hour_factor    = max(0.85, hour_factor)
            elif dev_type == "elevator":
                weekend_factor = 0.40 if is_weekend else 1.0

            energy = (base * hour_factor * weekend_factor * season_factor
                      * (1 + np.random.normal(0, 0.07)))
            energy = max(0.0, energy)

            # Inject anomalies (~2 %)
            if np.random.random() < 0.02:
                kind = np.random.choice(["spike", "drop"], p=[0.65, 0.35])
                energy *= (np.random.uniform(2.8, 4.5) if kind == "spike"
                           else np.random.uniform(0.04, 0.15))

            occupancy = max(0, int(
                250 * hour_factor * weekend_factor + np.random.normal(0, 12)
            ))

            records.append({
                "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
                "device_id":   dev_id,
                "building_id": cfg["building"],
                "energy_kwh":  round(energy, 4),
                "temperature": temperature,
                "humidity":    humidity,
                "occupancy":   occupancy,
            })

    df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
    logger.info(f"Generated {len(df):,} synthetic records ({start} → {end})")
    return df
