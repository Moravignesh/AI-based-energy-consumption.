from fastapi import APIRouter, Query
from app.ml.optimization import run_optimization, _peak_analysis, _device_stats
from app.services.data_store import data_store
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/recommendations", summary="Get AI optimization recommendations")
def get_recommendations(device_id: str = Query("ALL")):
    """
    Generate data-driven energy-saving recommendations including:
    load balancing, scheduling, device optimisation, HVAC, and sustainability strategies.
    Each recommendation includes estimated kWh and cost savings.
    """
    df = data_store.require()
    if device_id != "ALL":
        data_store.require_device(device_id)
    return run_optimization(df, device_id=device_id)


@router.get("/peak-analysis", summary="Peak usage analysis")
def peak_analysis_endpoint(device_id: str = "ALL"):
    """Returns peak/off-peak hours, load factor, and demand profile."""
    df = data_store.require()
    if device_id != "ALL":
        df = df[df["device_id"] == device_id]
    return _peak_analysis(df)


@router.get("/device-stats", summary="Per-device consumption statistics")
def device_statistics():
    """Total, mean, max, and std for each device — sorted by consumption."""
    df    = data_store.require()
    devs  = _device_stats(df)
    total = float(df["energy_kwh"].sum())
    devs["share_pct"] = (devs["total_kwh"] / total * 100).round(2)
    devs["cost_usd"]  = (devs["total_kwh"] * 0.12).round(2)
    return {"devices": devs.fillna(0).to_dict(orient="records")}


@router.get("/savings-summary", summary="Savings potential summary")
def savings_summary():
    """Quick summary of total potential savings without full recommendation details."""
    df  = data_store.require()
    opt = run_optimization(df)
    return {
        "total_potential_savings_kwh": opt["total_potential_savings_kwh"],
        "total_potential_savings_usd": opt["total_potential_savings_usd"],
        "savings_potential_pct":       opt["savings_potential_pct"],
        "recommendation_count":        len(opt["recommendations"]),
        "high_priority_count":         sum(1 for r in opt["recommendations"] if r["priority"]=="high"),
    }
