"""
NetElixIQ AI — AI Business Analyst API
LLM-powered forecast explanations, recommendations, and executive summaries.
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd

from backend.database import get_db, CampaignRecord
from backend.services.analyst.insights import (
    generate_forecast_explanation,
    generate_recommendations,
    generate_risk_analysis,
    generate_executive_summary,
    generate_anomaly_explanation,
)
from backend.api.forecast import _load_session_data, _get_or_train_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


def _df_from_session(session_id: str, db: Session) -> pd.DataFrame:
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == session_id
    ).all()
    if not records:
        raise HTTPException(404, f"No data for session '{session_id}'")
    return pd.DataFrame([{
        "date": r.date, "channel": r.channel, "spend": r.spend,
        "revenue": r.revenue, "roas": r.roas, "clicks": r.clicks,
        "impressions": r.impressions, "conversions": r.conversions,
    } for r in records])


@router.get("/analyst/{session_id}/forecast-explanation")
def get_forecast_explanation(
    session_id: str,
    horizon: int = 30,
    db: Session = Depends(get_db),
):
    """Generate a natural language explanation of the revenue forecast."""
    df = _df_from_session(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)

    explanation = generate_forecast_explanation(df, forecast_result, horizon=horizon)
    return {
        "session_id": session_id,
        "horizon": horizon,
        "explanation": explanation,
        "forecast_summary": forecast_result.get("summary", {}),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/analyst/{session_id}/recommendations")
def get_recommendations(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Generate prioritized marketing budget recommendations."""
    df = _df_from_session(session_id, db)
    recommendations = generate_recommendations(df)
    return {
        "session_id": session_id,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/analyst/{session_id}/risk")
def get_risk_analysis(
    session_id: str,
    horizon: int = 30,
    db: Session = Depends(get_db),
):
    """Generate a comprehensive risk analysis and risk score."""
    df = _df_from_session(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)

    risk = generate_risk_analysis(df, forecast_result)
    return {
        "session_id": session_id,
        **risk,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/analyst/{session_id}/executive-summary")
def get_executive_summary(
    session_id: str,
    horizon: int = 30,
    db: Session = Depends(get_db),
):
    """Generate a C-suite executive summary with forecast and recommendations."""
    df = _df_from_session(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)

    summary = generate_executive_summary(df, forecast_result, horizon=horizon)
    return {
        "session_id": session_id,
        "horizon": horizon,
        "summary": summary,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.post("/analyst/anomaly")
def explain_anomaly(
    channel: str,
    metric: str,
    current_value: float,
    expected_value: float,
):
    """
    Explain a specific marketing anomaly.
    Useful for ad-hoc investigation of unusual data points.
    """
    explanation = generate_anomaly_explanation(
        channel=channel,
        metric=metric,
        current_value=current_value,
        expected_value=expected_value,
    )
    return {
        "channel": channel,
        "metric": metric,
        "explanation": explanation,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
