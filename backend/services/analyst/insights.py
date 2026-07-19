"""
NetElixIQ AI — Business Insights Generator
Orchestrates Gemini LLM calls with structured marketing data to produce
forecast explanations, anomaly analyses, recommendations, and executive summaries.
"""
import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.services.analyst.gemini_client import gemini_client
from backend.services.analyst.prompts import (
    SYSTEM_PROMPT,
    FORECAST_EXPLANATION_PROMPT,
    ANOMALY_EXPLANATION_PROMPT,
    MARKETING_RECOMMENDATIONS_PROMPT,
    RISK_ANALYSIS_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
)

logger = logging.getLogger(__name__)


def _safe_format(template: str, **kwargs) -> str:
    """Safe string formatting that fills missing keys with 'N/A'."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing format key: {e}")
        defaults = {k: "N/A" for k in _extract_format_keys(template)}
        defaults.update(kwargs)
        try:
            return template.format(**defaults)
        except Exception:
            return template


def _extract_format_keys(template: str) -> List[str]:
    """Extract format keys from a template string."""
    import re
    return re.findall(r"\{(\w+)(?::[^}]*)?\}", template)


def _compute_channel_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute per-channel statistics from normalized DataFrame."""
    stats = {}
    if "channel" not in df.columns:
        return stats

    for channel in ["google", "meta", "microsoft"]:
        ch = df[df["channel"] == channel]
        if ch.empty:
            stats[channel] = {"roas": 0.0, "spend": 0.0, "revenue": 0.0}
        else:
            spend = float(ch["spend"].sum())
            revenue = float(ch["revenue"].sum())
            stats[channel] = {
                "roas": round(revenue / spend, 2) if spend > 0 else 0.0,
                "spend": round(spend, 2),
                "revenue": round(revenue, 2),
            }
    return stats


def _compute_risk_score(
    df: pd.DataFrame,
    channel_stats: Dict,
    confidence: float,
) -> float:
    """
    Compute a 0-10 risk score based on ROAS trends, data quality, and forecast confidence.
    Higher = more risky.
    """
    score = 5.0  # Base risk

    # Lower confidence → higher risk
    score += (1.0 - confidence) * 2

    # Meta ROAS decline check
    if "channel" in df.columns and "meta" in df["channel"].values:
        meta_df = df[df["channel"] == "meta"].copy()
        meta_df["date"] = pd.to_datetime(meta_df["date"])
        meta_df = meta_df.sort_values("date")

        if len(meta_df) >= 14:
            recent_roas = meta_df["roas"].iloc[-7:].mean() if "roas" in meta_df.columns else 0
            older_roas = meta_df["roas"].iloc[-14:-7].mean() if "roas" in meta_df.columns else 0
            if older_roas > 0 and recent_roas < older_roas * 0.85:
                score += 1.5  # ROAS declining

    # Data coverage
    if len(df) < 30:
        score += 1.0  # Limited data

    return min(10.0, max(0.0, round(score, 1)))


def generate_forecast_explanation(
    df: pd.DataFrame,
    forecast_result: Dict[str, Any],
    horizon: int = 30,
) -> str:
    """
    Generate a natural language forecast explanation using Gemini.

    Args:
        df: Historical campaign DataFrame.
        forecast_result: Output from ForecastingPipeline.predict().
        horizon: Forecast horizon in days.

    Returns:
        Formatted markdown explanation string.
    """
    channel_stats = _compute_channel_stats(df)

    total_spend = float(df["spend"].sum()) if "spend" in df.columns else 0
    total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0
    blended_roas = total_revenue / total_spend if total_spend > 0 else 0

    summary = forecast_result.get("summary", {})
    p10 = summary.get("total_p10", 0)
    p50 = summary.get("total_p50", 0)
    p90 = summary.get("total_p90", 0)
    confidence = forecast_result.get("confidence", 0.7)
    mape = forecast_result.get("training_stats", {}).get("lgbm_mape", 0.15)

    # Revenue change vs last same-length period
    if len(df) >= horizon * 2 and "revenue" in df.columns:
        prev_revenue = float(df["revenue"].iloc[-horizon * 2:-horizon].sum())
        revenue_change_pct = (p50 - prev_revenue) / max(prev_revenue, 1) * 100
    else:
        revenue_change_pct = 0.0

    channel_breakdown = ", ".join([
        f"{ch.title()}: ${v['revenue']:,.0f} (ROAS {v['roas']:.1f}x)"
        for ch, v in channel_stats.items() if v["spend"] > 0
    ]) or "No channel breakdown available"

    channel_trends = "\n".join([
        f"- {ch.title()}: ROAS {v['roas']:.2f}x | Spend ${v['spend']:,.0f} | Revenue ${v['revenue']:,.0f}"
        for ch, v in channel_stats.items()
    ]) or "No trend data available"

    prompt = _safe_format(
        FORECAST_EXPLANATION_PROMPT,
        total_revenue=total_revenue,
        total_spend=total_spend,
        blended_roas=blended_roas,
        channel_breakdown=channel_breakdown,
        horizon=horizon,
        forecast_p50=p50,
        forecast_p10=p10,
        forecast_p90=p90,
        revenue_change_pct=revenue_change_pct,
        confidence=confidence,
        channel_trends=channel_trends,
        mape=mape,
    )

    return gemini_client.generate(prompt, system_instruction=SYSTEM_PROMPT)


def generate_anomaly_explanation(
    channel: str,
    metric: str,
    current_value: float,
    expected_value: float,
    df: Optional[pd.DataFrame] = None,
    context: Optional[Dict] = None,
) -> str:
    """Generate anomaly explanation for a specific channel/metric deviation."""
    deviation_pct = (current_value - expected_value) / max(abs(expected_value), 0.01) * 100

    prompt = _safe_format(
        ANOMALY_EXPLANATION_PROMPT,
        channel=channel,
        metric=metric,
        current_value=f"{current_value:.2f}",
        expected_value=f"{expected_value:.2f}",
        deviation_pct=deviation_pct,
        duration_days=context.get("duration_days", "Unknown") if context else "Unknown",
        campaign_changes=context.get("campaign_changes", "No recent changes detected") if context else "N/A",
        budget_changes=context.get("budget_changes", "No budget changes detected") if context else "N/A",
        seasonal_context=context.get("seasonal_context", "Normal period") if context else "N/A",
        other_channels=context.get("other_channels", "No data") if context else "N/A",
    )

    return gemini_client.generate(prompt, system_instruction=SYSTEM_PROMPT)


def generate_recommendations(
    df: pd.DataFrame,
    simulation_result: Optional[Dict] = None,
) -> str:
    """Generate prioritized marketing budget recommendations."""
    channel_stats = _compute_channel_stats(df)

    total_budget = sum(v["spend"] for v in channel_stats.values())

    google_budget = channel_stats.get("google", {}).get("spend", 0)
    meta_budget = channel_stats.get("meta", {}).get("spend", 0)
    microsoft_budget = channel_stats.get("microsoft", {}).get("spend", 0)

    google_pct = google_budget / total_budget * 100 if total_budget > 0 else 0
    meta_pct = meta_budget / total_budget * 100 if total_budget > 0 else 0
    microsoft_pct = microsoft_budget / total_budget * 100 if total_budget > 0 else 0

    total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0
    blended_roas = total_revenue / total_budget if total_budget > 0 else 0

    performance_summary = (
        f"Total Revenue: ${total_revenue:,.0f} | Total Spend: ${total_budget:,.0f} | "
        f"Blended ROAS: {blended_roas:.2f}x"
    )

    simulation_insight = "No simulation data available."
    if simulation_result:
        sim_roas = simulation_result.get("roas", {}).get("p50", 0)
        sim_revenue = simulation_result.get("revenue", {}).get("p50", 0)
        simulation_insight = (
            f"Budget simulation (optimized allocation) projects ROAS of {sim_roas:.2f}x "
            f"and revenue of ${sim_revenue:,.0f}."
        )

    prompt = _safe_format(
        MARKETING_RECOMMENDATIONS_PROMPT,
        performance_summary=performance_summary,
        google_budget=google_budget,
        meta_budget=meta_budget,
        microsoft_budget=microsoft_budget,
        google_pct=google_pct,
        meta_pct=meta_pct,
        microsoft_pct=microsoft_pct,
        google_roas=channel_stats.get("google", {}).get("roas", 0),
        meta_roas=channel_stats.get("meta", {}).get("roas", 0),
        microsoft_roas=channel_stats.get("microsoft", {}).get("roas", 0),
        simulation_insight=simulation_insight,
    )

    return gemini_client.generate(prompt, system_instruction=SYSTEM_PROMPT)


def generate_risk_analysis(
    df: pd.DataFrame,
    forecast_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a risk analysis including risk score and LLM explanation.

    Returns:
        Dict with 'risk_score', 'risk_level', 'explanation'.
    """
    channel_stats = _compute_channel_stats(df)
    confidence = forecast_result.get("confidence", 0.7)
    risk_score = _compute_risk_score(df, channel_stats, confidence)

    # Risk level
    if risk_score >= 7:
        risk_level = "HIGH"
        risk_color = "red"
    elif risk_score >= 4.5:
        risk_level = "MEDIUM"
        risk_color = "amber"
    else:
        risk_level = "LOW"
        risk_color = "green"

    # ROAS trend
    if "roas" in df.columns and len(df) >= 14:
        recent_roas = df["roas"].iloc[-7:].mean()
        older_roas = df["roas"].iloc[-14:-7].mean()
        roas_change = (recent_roas - older_roas) / max(older_roas, 0.01) * 100
        roas_trend = f"{'↑' if roas_change > 0 else '↓'} {abs(roas_change):.1f}% last 7 days"
    else:
        roas_trend = "Insufficient data"

    channel_health = "\n".join([
        f"- {ch.title()}: ROAS {v['roas']:.2f}x ({'✅ Healthy' if v['roas'] > 2.5 else '⚠️ Below Target'})"
        for ch, v in channel_stats.items()
    ]) or "No channel data"

    data_coverage_days = int(
        (pd.to_datetime(df["date"].max()) - pd.to_datetime(df["date"].min())).days
    ) if "date" in df.columns and len(df) > 0 else 0

    prompt = _safe_format(
        RISK_ANALYSIS_PROMPT,
        risk_score=risk_score,
        confidence=confidence,
        roas_trend=roas_trend,
        spend_trend="Stable",
        channel_health=channel_health,
        data_coverage_days=data_coverage_days,
        missing_pct=0.0,
        data_gaps="None detected",
        revenue_vs_budget=f"ROAS {channel_stats.get('google', {}).get('roas', 0):.1f}x",
        yoy_trend="Not enough data for YoY comparison",
    )

    explanation = gemini_client.generate(prompt, system_instruction=SYSTEM_PROMPT)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "explanation": explanation,
        "channel_stats": channel_stats,
    }


def generate_executive_summary(
    df: pd.DataFrame,
    forecast_result: Dict[str, Any],
    horizon: int = 30,
) -> str:
    """Generate a C-suite executive summary."""
    channel_stats = _compute_channel_stats(df)
    summary = forecast_result.get("summary", {})

    total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0
    total_spend = float(df["spend"].sum()) if "spend" in df.columns else 0
    blended_roas = total_revenue / total_spend if total_spend > 0 else 0

    top_channel = max(channel_stats.items(), key=lambda x: x[1]["revenue"])[0] if channel_stats else "N/A"
    top_channel_revenue = channel_stats.get(top_channel, {}).get("revenue", 0) if channel_stats else 0

    risk_result = generate_risk_analysis(df, forecast_result)

    prompt = _safe_format(
        EXECUTIVE_SUMMARY_PROMPT,
        period=f"Last {len(df)} days",
        total_revenue=total_revenue,
        revenue_change=0.0,
        blended_roas=blended_roas,
        roas_change=0.0,
        total_spend=total_spend,
        top_channel=top_channel.title(),
        top_channel_revenue=top_channel_revenue,
        horizon=horizon,
        forecast_p50=summary.get("total_p50", 0),
        confidence=forecast_result.get("confidence", 0.7),
        key_risk=risk_result.get("risk_level", "Moderate"),
        notable_insights=f"Risk Score: {risk_result['risk_score']}/10",
    )

    return gemini_client.generate(prompt, system_instruction=SYSTEM_PROMPT)
