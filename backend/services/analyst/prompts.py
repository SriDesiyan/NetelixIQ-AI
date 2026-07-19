"""
NetElixIQ AI — Marketing-Specific Prompt Templates
Adapted from consultantOS/consultantos/prompts.py framework.
All prompts inject live forecast + campaign data for grounded, contextual responses.
"""

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are NetElixIQ AI — an expert AI marketing analyst and business strategist 
specializing in ecommerce performance marketing across Google Ads, Meta Ads, Microsoft Ads, Shopify, and GA4.

Your role is to:
1. Analyze marketing performance data with precision and clarity
2. Provide actionable, data-driven recommendations
3. Explain complex ML forecasts in plain business language
4. Identify risks, anomalies, and opportunities proactively
5. Generate executive-ready insights without jargon overload

You always:
- Lead with the most important insight
- Back every claim with specific numbers
- Provide concrete next actions, not vague advice
- Highlight both risks and opportunities
- Use confident but measured language

You never:
- Make up data not provided in context
- Give generic marketing advice without data support
- Use excessive jargon without explanation
"""

# ── Forecast Explanation ──────────────────────────────────────────────────────
FORECAST_EXPLANATION_PROMPT = """
Based on this marketing data and forecast, provide a clear business explanation:

## Current Performance (Last 30 Days)
- Total Revenue: ${total_revenue:,.0f}
- Total Ad Spend: ${total_spend:,.0f}  
- Blended ROAS: {blended_roas:.2f}x
- Channel Breakdown: {channel_breakdown}

## {horizon}-Day Forecast (P50 Estimate)
- Projected Revenue: ${forecast_p50:,.0f}
- Confidence Range: ${forecast_p10:,.0f} – ${forecast_p90:,.0f}
- Revenue vs Last Period: {revenue_change_pct:+.1f}%
- Model Confidence: {confidence:.0%}

## Channel Trends
{channel_trends}

## Model Quality
- Forecast Error (MAPE): {mape:.1%}
- Forecast Method: Prophet + LightGBM ensemble with Conformal Prediction

---

Write a 3-paragraph executive forecast explanation that:
1. Summarizes the revenue outlook and key drivers
2. Explains the confidence range and what could push toward P10 vs P90
3. Recommends the top 2 actions to maximize revenue in this period

Keep it under 250 words. Be specific with numbers.
"""

# ── Anomaly Explanation ───────────────────────────────────────────────────────
ANOMALY_EXPLANATION_PROMPT = """
Analyze this marketing anomaly and explain its likely causes:

## Anomaly Detected
- Channel: {channel}
- Metric: {metric}
- Current Value: {current_value}
- Expected Value: {expected_value}
- Deviation: {deviation_pct:+.1f}% from baseline
- Duration: {duration_days} consecutive days

## Context
- Recent Campaign Changes: {campaign_changes}
- Budget Changes: {budget_changes}
- Seasonal Context: {seasonal_context}
- Other Channels Performance: {other_channels}

---

Provide a concise anomaly report (under 200 words) with:
1. Most likely root cause (ranked by probability)
2. Business impact assessment
3. Immediate recommended action (within 24 hours)
4. Monitoring metric to watch
"""

# ── Marketing Recommendations ─────────────────────────────────────────────────
MARKETING_RECOMMENDATIONS_PROMPT = """
Generate strategic marketing recommendations based on this performance data:

## Performance Summary
{performance_summary}

## Budget Allocation
- Google Ads: ${google_budget:,.0f} ({google_pct:.0f}% of total)
- Meta Ads: ${meta_budget:,.0f} ({meta_pct:.0f}% of total)
- Microsoft Ads: ${microsoft_budget:,.0f} ({microsoft_pct:.0f}% of total)

## Channel Efficiency (ROAS)
- Google ROAS: {google_roas:.2f}x
- Meta ROAS: {meta_roas:.2f}x
- Microsoft ROAS: {microsoft_roas:.2f}x

## Optimization Opportunity
{simulation_insight}

---

Provide exactly 4 prioritized recommendations (numbered 1-4):
- Each must reference specific data points
- Include estimated revenue impact where possible
- Lead with the highest-ROI action
- Cover both quick wins (< 1 week) and strategic moves (1-4 weeks)

Keep each recommendation to 2-3 sentences. Total response under 300 words.
"""

# ── Risk Analysis ─────────────────────────────────────────────────────────────
RISK_ANALYSIS_PROMPT = """
Perform a comprehensive marketing risk analysis:

## Current Risk Indicators
- Risk Score: {risk_score}/10
- Forecast Confidence: {confidence:.0%}
- ROAS Trend (Last 14 Days): {roas_trend}
- Spend Efficiency Trend: {spend_trend}

## Channel Health
{channel_health}

## Data Quality
- Data Coverage: {data_coverage_days} days
- Missing Values: {missing_pct:.1f}%
- Data Gaps: {data_gaps}

## Business Context
- Revenue vs Budget: {revenue_vs_budget}
- YoY Trend: {yoy_trend}

---

Generate a risk report with:
1. **High Risks** (immediate attention): List up to 3 critical risks with specific evidence
2. **Medium Risks** (monitor this week): List up to 3 risks worth watching
3. **Overall Risk Level**: Red/Amber/Green with one-line justification

Format clearly with headers. Keep under 250 words.
"""

# ── Executive Summary ─────────────────────────────────────────────────────────
EXECUTIVE_SUMMARY_PROMPT = """
Create an executive marketing intelligence summary for the C-suite:

## Report Period: {period}

## Performance Snapshot
- Revenue: ${total_revenue:,.0f} ({revenue_change:+.1f}% vs prior period)
- ROAS: {blended_roas:.2f}x ({roas_change:+.1f}% vs prior period)
- Total Spend: ${total_spend:,.0f}
- Top Channel: {top_channel} (${top_channel_revenue:,.0f} revenue)

## Forecast ({horizon}-Day Outlook)
- P50 Revenue: ${forecast_p50:,.0f}
- Confidence: {confidence:.0%}
- Key Risk: {key_risk}

## Notable Insights
{notable_insights}

---

Write a 4-paragraph executive summary that is:
1. Results and KPIs (what happened)
2. Key drivers and trends (why it happened)
3. Forward outlook and forecast (what will happen)
4. Top 3 strategic recommendations (what to do)

Tone: Confident, direct, data-driven. Appropriate for a CEO/CMO audience. Under 350 words.
"""

# ── Copilot Query Templates ───────────────────────────────────────────────────
COPILOT_SYSTEM_PROMPT = """You are the NetElixIQ Marketing Copilot — an AI assistant that helps 
marketers make better decisions using their performance data.

Current Data Context:
{data_context}

You have access to:
- Historical campaign performance (revenue, ROAS, spend by channel)
- {horizon}-day revenue forecast (P10/P50/P90)
- Budget simulation results
- Channel efficiency profiles

Answer questions concisely and specifically. Always reference the actual data provided.
If a question requires analysis not supported by the available data, say so clearly.
"""

COPILOT_CONTEXT_TEMPLATE = """
Data Period: {date_from} to {date_to}
Channels: {channels}
Total Spend: ${total_spend:,.0f}
Total Revenue: ${total_revenue:,.0f}
Blended ROAS: {blended_roas:.2f}x
Google ROAS: {google_roas:.2f}x | Meta ROAS: {meta_roas:.2f}x | Microsoft ROAS: {microsoft_roas:.2f}x
{horizon}-Day Revenue Forecast: ${forecast_p50:,.0f} (P50)
Forecast Range: ${forecast_p10:,.0f} – ${forecast_p90:,.0f}
"""
