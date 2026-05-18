from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import SimulationRequest
from app.ml.simulation import run_simulation, SCENARIO_META
from app.services.data_store import data_store
from app.database import get_db, SimulationRun
from app.core.logging import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)


@router.post("/run", summary="Run scenario simulation")
def simulation_run(req: SimulationRequest, db: Session = Depends(get_db)):
    """
    Simulate energy impact of operational changes:
    - **occupancy_change**: Alter building occupancy level
    - **temperature_change**: Shift outdoor temperature (HVAC load)
    - **device_shutdown**: Schedule device downtime
    - **peak_reduction**: Apply demand-response / peak shaving
    """
    df     = data_store.require()
    result = run_simulation(df, scenario=req.scenario,
                             params=req.parameters, device_id=req.device_id)
    # Persist run
    db.add(SimulationRun(
        run_id=result["run_id"], scenario=req.scenario,
        parameters=json.dumps(req.parameters),
        baseline_kwh=result["baseline_kwh"],
        simulated_kwh=result["simulated_kwh"],
        energy_savings_kwh=result["energy_savings_kwh"],
        cost_savings_usd=result["cost_savings_usd"],
        savings_percent=result["savings_percent"],
    ))
    db.commit()
    return result


@router.get("/scenarios", summary="List available simulation scenarios")
def list_scenarios():
    """Returns all supported scenarios with their configurable parameters."""
    return {"scenarios": [
        {"key": k, "label": v["label"], "description": v["description"],
         "parameters": v["parameters"]}
        for k, v in SCENARIO_META.items()
    ]}


@router.get("/history", summary="Simulation run history")
def simulation_history(limit: int = 20, db: Session = Depends(get_db)):
    """Returns the last N simulation runs with key metrics."""
    runs = db.query(SimulationRun).order_by(SimulationRun.created_at.desc()).limit(limit).all()
    return {"runs": [
        {"run_id": r.run_id, "scenario": r.scenario,
         "energy_savings_kwh": r.energy_savings_kwh,
         "cost_savings_usd": r.cost_savings_usd,
         "savings_percent": r.savings_percent,
         "created_at": r.created_at.isoformat()}
        for r in runs
    ]}
