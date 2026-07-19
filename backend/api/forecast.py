"""
NetElixIQ AI — Forecasting API
Generates probabilistic revenue/ROAS forecasts with P10/P50/P90 intervals.
"""
import logging
import json
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import pandas as pd

from backend.config import settings
from backend.database import get_db, CampaignRecord, ForecastResult
from backend.services.forecasting.pipeline import ForecastingPipeline
from backend.utils.cache import cache_get, cache_set, make_cache_key

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory pipeline cache (per session)
_pipeline_cache: dict = {}


def _load_session_data(session_id: str, db: Session) -> pd.DataFrame:
    """Load campaign records for a session into a DataFrame."""
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == session_id
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No data for session '{session_id}'")

    return pd.DataFrame([{
        "date": r.date,
        "channel": r.channel,
        "campaign": r.campaign,
        "impressions": r.impressions,
        "clicks": r.clicks,
        "spend": r.spend,
        "conversions": r.conversions,
        "revenue": r.revenue,
        "roas": r.roas,
        "ctr": r.ctr,
        "cvr": r.cvr,
        "cpc": r.cpc,
    } for r in records])


def _get_or_train_pipeline(session_id: str, df: pd.DataFrame) -> ForecastingPipeline:
    """Get cached pipeline or train a new one."""
    if session_id in _pipeline_cache:
        return _pipeline_cache[session_id]

    # Check if a saved model exists
    model_path = f"pickle/pipeline_{session_id[:8]}.pkl"
    try:
        pipeline = ForecastingPipeline.load(model_path)
        _pipeline_cache[session_id] = pipeline
        return pipeline
    except Exception:
        pass

    # Train new pipeline
    logger.info(f"Training new pipeline for session {session_id[:8]}...")
    pipeline = ForecastingPipeline(model_artifact_path=model_path)
    pipeline.fit(df, target_col="revenue")

    # Save for next time
    try:
        pipeline.save(model_path)
    except Exception as e:
        logger.warning(f"Could not save pipeline: {e}")

    _pipeline_cache[session_id] = pipeline
    return pipeline


@router.post("/forecast/{session_id}")
def generate_forecast(
    session_id: str,
    horizon: int = Query(default=30, ge=1, le=90, description="Forecast horizon (30, 60, or 90 days)"),
    metric: str = Query(default="revenue", pattern="^(revenue|roas|spend)$"),
    retrain: bool = Query(default=False, description="Force model retraining"),
    db: Session = Depends(get_db),
):
    """
    Generate a probabilistic forecast for the specified session and horizon.

    Returns P10/P50/P90 daily values with confidence intervals.
    """
    # Cache key
    cache_key = make_cache_key(session_id, horizon, metric)
    if not retrain:
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"Forecast cache HIT: {session_id[:8]} | horizon={horizon}")
            return cached

    # Load data
    df = _load_session_data(session_id, db)

    if retrain and session_id in _pipeline_cache:
        del _pipeline_cache[session_id]

    # Get/train pipeline
    try:
        pipeline = _get_or_train_pipeline(session_id, df)
    except Exception as e:
        logger.error(f"Pipeline training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

    # Generate forecast
    try:
        result = pipeline.predict(horizon=horizon)
    except Exception as e:
        logger.error(f"Forecast prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast prediction failed: {str(e)}")

    # Enrich with session meta
    result["session_id"] = session_id
    result["horizon"] = horizon
    result["metric"] = metric
    result["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Persist to DB
    try:
        db.add(ForecastResult(
            session_id=session_id,
            horizon_days=horizon,
            metric=metric,
            forecast_json=json.dumps(result.get("forecast", [])),
            model_weights=result.get("model_weights"),
            mape=result.get("training_stats", {}).get("lgbm_mape"),
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist forecast: {e}")

    # Cache result
    cache_set(cache_key, result, ttl=1800)

    return result


@router.get("/forecast/{session_id}/channel-contribution")
def get_channel_contribution(
    session_id: str,
    horizon: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """
    Get forecasted revenue contribution by channel.
    Based on historical channel mix ratios applied to the total revenue forecast.
    """
    df = _load_session_data(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)

    # Channel mix from historical data
    if "channel" in df.columns:
        channel_revenue = df.groupby("channel")["revenue"].sum()
        total_rev = channel_revenue.sum()
        channel_mix = {
            ch: round(float(rev / total_rev * 100), 1) if total_rev > 0 else 0
            for ch, rev in channel_revenue.items()
        }
    else:
        channel_mix = {}

    p50_total = forecast_result.get("summary", {}).get("total_p50", 0)

    return {
        "session_id": session_id,
        "horizon": horizon,
        "total_forecast_p50": p50_total,
        "channel_contribution": {
            ch: {
                "revenue_share_pct": pct,
                "projected_revenue": round(p50_total * pct / 100, 2),
            }
            for ch, pct in channel_mix.items()
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/forecast/{session_id}/history")
def get_forecast_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """List all previous forecasts for a session."""
    forecasts = db.query(ForecastResult).filter(
        ForecastResult.session_id == session_id
    ).order_by(ForecastResult.created_at.desc()).all()

    return {
        "session_id": session_id,
        "forecasts": [
            {
                "id": f.id,
                "horizon_days": f.horizon_days,
                "metric": f.metric,
                "mape": f.mape,
                "created_at": f.created_at.isoformat(),
            }
            for f in forecasts
        ],
    }
