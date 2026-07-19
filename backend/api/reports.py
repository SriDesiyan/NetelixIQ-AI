"""
NetElixIQ AI — Reports API
PDF and data export endpoints.
"""
import logging
import io
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd

from backend.database import get_db, CampaignRecord
from backend.api.forecast import _load_session_data, _get_or_train_pipeline
from backend.services.analyst.insights import generate_executive_summary, generate_risk_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/{session_id}/pdf")
def export_pdf_report(
    session_id: str,
    horizon: int = 30,
    db: Session = Depends(get_db),
):
    """Export a comprehensive PDF report for a session."""
    df = _load_session_data(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)
    risk = generate_risk_analysis(df, forecast_result)
    summary_text = generate_executive_summary(df, forecast_result, horizon=horizon)

    # Build PDF using reportlab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "Title", parent=styles["Title"],
            fontSize=24, textColor=colors.HexColor("#1a56db"),
        )
        story.append(Paragraph("NetElixIQ AI — Marketing Intelligence Report", title_style))
        story.append(Paragraph(f"Session: {session_id[:8]} | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a56db")))
        story.append(Spacer(1, 0.25 * inch))

        # KPI Summary
        total_spend = df["spend"].sum() if "spend" in df.columns else 0
        total_revenue = df["revenue"].sum() if "revenue" in df.columns else 0
        blended_roas = total_revenue / total_spend if total_spend > 0 else 0
        forecast_p50 = forecast_result.get("summary", {}).get("total_p50", 0)

        story.append(Paragraph("📊 Performance Summary", styles["Heading1"]))
        kpi_data = [
            ["Metric", "Value"],
            ["Total Revenue", f"${total_revenue:,.0f}"],
            ["Total Spend", f"${total_spend:,.0f}"],
            ["Blended ROAS", f"{blended_roas:.2f}x"],
            [f"{horizon}-Day Forecast (P50)", f"${forecast_p50:,.0f}"],
            ["Forecast Confidence", f"{forecast_result.get('confidence', 0):.0%}"],
            ["Risk Score", f"{risk['risk_score']}/10 ({risk['risk_level']})"],
        ]
        table = Table(kpi_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a56db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.25 * inch))

        # Executive Summary
        story.append(Paragraph("📋 Executive Summary", styles["Heading1"]))
        for line in summary_text.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line.replace("**", "").replace("*", ""), styles["Normal"]))
                story.append(Spacer(1, 0.08 * inch))
        story.append(Spacer(1, 0.25 * inch))

        # Risk Analysis
        story.append(Paragraph("⚠️ Risk Analysis", styles["Heading1"]))
        story.append(Paragraph(
            f"Risk Level: {risk['risk_level']} | Score: {risk['risk_score']}/10",
            styles["Normal"]
        ))
        for line in risk.get("explanation", "").split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip().replace("**", "").replace("*", ""), styles["Normal"]))
                story.append(Spacer(1, 0.05 * inch))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=netelixiq_report_{session_id[:8]}.pdf"
            },
        )

    except ImportError:
        # Fallback: return plain text report
        report_text = f"""NetElixIQ AI Marketing Intelligence Report
Generated: {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
Session: {session_id}

=== PERFORMANCE SUMMARY ===
Total Revenue: ${total_revenue:,.0f}
Total Spend: ${total_spend:,.0f}
Blended ROAS: {blended_roas:.2f}x
{horizon}-Day Forecast (P50): ${forecast_p50:,.0f}
Confidence: {forecast_result.get('confidence', 0):.0%}
Risk Score: {risk['risk_score']}/10 ({risk['risk_level']})

=== EXECUTIVE SUMMARY ===
{summary_text}

=== RISK ANALYSIS ===
{risk.get('explanation', '')}
"""
        return StreamingResponse(
            io.BytesIO(report_text.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=netelixiq_report_{session_id[:8]}.txt"},
        )


@router.get("/reports/{session_id}/csv")
def export_forecast_csv(
    session_id: str,
    horizon: int = 30,
    db: Session = Depends(get_db),
):
    """Export forecast data as CSV."""
    df = _load_session_data(session_id, db)
    pipeline = _get_or_train_pipeline(session_id, df)
    forecast_result = pipeline.predict(horizon=horizon)

    forecast_df = pd.DataFrame(forecast_result.get("forecast", []))
    csv_content = forecast_df.to_csv(index=False)

    return StreamingResponse(
        io.BytesIO(csv_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=forecast_{session_id[:8]}_{horizon}d.csv"},
    )
