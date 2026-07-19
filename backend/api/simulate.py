"""
NetElixIQ AI — Budget Simulation API
Monte Carlo simulation of revenue/ROAS for arbitrary budget allocations.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, CampaignRecord, SimulationResult
from backend.services.simulation.budget_sim import BudgetSimulator
import pandas as pd
import json

logger = logging.getLogger(__name__)
router = APIRouter()


class BudgetSimulationRequest(BaseModel):
    session_id: str = Field(..., description="Data session ID from ingestion")
    google_budget: float = Field(..., ge=0, description="Google Ads budget (USD)")
    meta_budget: float = Field(..., ge=0, description="Meta Ads budget (USD)")
    microsoft_budget: float = Field(0.0, ge=0, description="Microsoft Ads budget (USD)")
    horizon_days: int = Field(30, ge=1, le=90, description="Budget period in days")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "google_budget": 15000,
                "meta_budget": 8000,
                "microsoft_budget": 3000,
                "horizon_days": 30,
            }
        }


@router.post("/simulate/budget")
def run_budget_simulation(
    request: BudgetSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Run Monte Carlo budget simulation (2,000 scenarios).

    Given a budget allocation across channels, returns:
    - Revenue distribution (P10/P50/P90)
    - Blended ROAS distribution
    - Channel revenue contribution
    - Confidence score
    """
    # Load historical data for calibration
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == request.session_id
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No data for session '{request.session_id}'")

    df = pd.DataFrame([{
        "date": r.date,
        "channel": r.channel,
        "spend": r.spend,
        "revenue": r.revenue,
        "roas": r.roas,
    } for r in records])

    # Calibrate simulator on historical data
    simulator = BudgetSimulator(n_simulations=settings.monte_carlo_simulations)
    simulator.calibrate_from_data(df)

    # Run simulation
    result = simulator.simulate(
        google_budget=request.google_budget,
        meta_budget=request.meta_budget,
        microsoft_budget=request.microsoft_budget,
        horizon_days=request.horizon_days,
    )

    # Persist result
    try:
        db.add(SimulationResult(
            session_id=request.session_id,
            google_budget=request.google_budget,
            meta_budget=request.meta_budget,
            microsoft_budget=request.microsoft_budget,
            expected_revenue_p50=result.get("revenue", {}).get("p50"),
            expected_roas_p50=result.get("roas", {}).get("p50"),
            channel_mix_json=result.get("channel_mix"),
            confidence=result.get("confidence"),
            simulation_json=json.dumps(result),
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist simulation: {e}")

    result["session_id"] = request.session_id
    result["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return result


@router.get("/simulate/{session_id}/optimal")
def get_optimal_budget(
    session_id: str,
    total_budget: float = 25000,
    horizon_days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Find the optimal budget allocation across channels to maximize revenue P50.
    Tests 9 allocation scenarios and returns the best.
    """
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == session_id
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No data for session '{session_id}'")

    df = pd.DataFrame([{
        "date": r.date, "channel": r.channel, "spend": r.spend, "revenue": r.revenue
    } for r in records])

    simulator = BudgetSimulator()
    simulator.calibrate_from_data(df)

    # Grid search over allocations
    best_result = None
    best_revenue = -1
    best_allocation = {}

    for google_pct in [0.40, 0.50, 0.60]:
        for meta_pct in [0.25, 0.35, 0.45]:
            microsoft_pct = max(0, 1.0 - google_pct - meta_pct)
            if microsoft_pct < 0:
                continue

            result = simulator.simulate(
                google_budget=total_budget * google_pct,
                meta_budget=total_budget * meta_pct,
                microsoft_budget=total_budget * microsoft_pct,
                horizon_days=horizon_days,
            )

            rev_p50 = result.get("revenue", {}).get("p50", 0)
            if rev_p50 > best_revenue:
                best_revenue = rev_p50
                best_result = result
                best_allocation = {
                    "google_pct": google_pct,
                    "meta_pct": meta_pct,
                    "microsoft_pct": microsoft_pct,
                    "google_budget": total_budget * google_pct,
                    "meta_budget": total_budget * meta_pct,
                    "microsoft_budget": total_budget * microsoft_pct,
                }

    return {
        "session_id": session_id,
        "total_budget": total_budget,
        "optimal_allocation": best_allocation,
        "simulation_result": best_result,
        "note": "Optimized to maximize P50 revenue using grid search.",
    }
