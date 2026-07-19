"""
NetElixIQ AI — Marketing Copilot API
Conversational AI interface for natural language marketing Q&A.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db, CampaignRecord, ChatSession
from backend.services.analyst.gemini_client import gemini_client
from backend.services.analyst.prompts import COPILOT_SYSTEM_PROMPT, COPILOT_CONTEXT_TEMPLATE

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_HISTORY = 10  # Keep last 10 turns in context


class CopilotMessage(BaseModel):
    session_id: str = Field(..., description="Data session ID")
    chat_id: str = Field(default="", description="Chat session ID (auto-created if empty)")
    message: str = Field(..., min_length=1, max_length=2000)
    horizon: int = Field(default=30, ge=1, le=90)


class CopilotResponse(BaseModel):
    chat_id: str
    message: str
    response: str
    timestamp: str


def _build_data_context(session_id: str, horizon: int, db: Session) -> str:
    """Build a data context string for the copilot system prompt."""
    records = db.query(CampaignRecord).filter(
        CampaignRecord.upload_session_id == session_id
    ).all()

    if not records:
        return "No data loaded. User should upload data first."

    import pandas as pd
    df = pd.DataFrame([{
        "date": r.date, "channel": r.channel, "spend": r.spend, "revenue": r.revenue
    } for r in records])

    total_spend = float(df["spend"].sum())
    total_revenue = float(df["revenue"].sum())
    channels = list(df["channel"].unique())

    channel_roas = {}
    for ch in ["google", "meta", "microsoft"]:
        ch_df = df[df["channel"] == ch]
        if not ch_df.empty and ch_df["spend"].sum() > 0:
            channel_roas[ch] = round(float(ch_df["revenue"].sum() / ch_df["spend"].sum()), 2)
        else:
            channel_roas[ch] = 0.0

    return COPILOT_CONTEXT_TEMPLATE.format(
        date_from=df["date"].min(),
        date_to=df["date"].max(),
        channels=", ".join(channels),
        total_spend=total_spend,
        total_revenue=total_revenue,
        blended_roas=round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
        google_roas=channel_roas.get("google", 0),
        meta_roas=channel_roas.get("meta", 0),
        microsoft_roas=channel_roas.get("microsoft", 0),
        horizon=horizon,
        forecast_p50=total_revenue * 1.08 / 4,  # Simple estimate
        forecast_p10=total_revenue * 0.9 / 4,
        forecast_p90=total_revenue * 1.25 / 4,
    )


@router.post("/copilot/chat", response_model=CopilotResponse)
def chat_with_copilot(
    request: CopilotMessage,
    db: Session = Depends(get_db),
):
    """
    Send a message to the Marketing Copilot.

    Examples:
    - "Why is Meta ROAS decreasing?"
    - "Which channel should receive more budget?"
    - "How much revenue will I lose if Google budget drops by 20%?"
    - "Generate a risk analysis for my campaigns"
    """
    import uuid

    # Get or create chat session
    chat_id = request.chat_id or str(uuid.uuid4())
    chat_session = db.query(ChatSession).filter(ChatSession.session_id == chat_id).first()

    if not chat_session:
        chat_session = ChatSession(session_id=chat_id, messages_json="[]")
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    # Load message history
    try:
        messages = json.loads(chat_session.messages_json or "[]")
    except Exception:
        messages = []

    # Build data context for system prompt
    data_context = _build_data_context(request.session_id, request.horizon, db)
    system_instruction = COPILOT_SYSTEM_PROMPT.format(
        data_context=data_context,
        horizon=request.horizon,
    )

    # Append user message
    messages.append({"role": "user", "content": request.message})

    # Keep only last N turns
    messages = messages[-(MAX_HISTORY * 2):]

    # Generate response
    try:
        response_text = gemini_client.generate_with_history(
            messages=messages,
            system_instruction=system_instruction,
        )
    except Exception as e:
        logger.error(f"Copilot generation failed: {e}")
        response_text = (
            "I encountered an error processing your request. "
            "Please try rephrasing your question or check your API configuration."
        )

    # Append assistant response
    messages.append({"role": "model", "content": response_text})

    # Update chat session
    chat_session.messages_json = json.dumps(messages)
    db.commit()

    return CopilotResponse(
        chat_id=chat_id,
        message=request.message,
        response=response_text,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@router.get("/copilot/{chat_id}/history")
def get_chat_history(chat_id: str, db: Session = Depends(get_db)):
    """Retrieve conversation history for a chat session."""
    session = db.query(ChatSession).filter(ChatSession.session_id == chat_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        messages = json.loads(session.messages_json or "[]")
    except Exception:
        messages = []

    return {
        "chat_id": chat_id,
        "messages": messages,
        "message_count": len(messages),
        "created_at": session.created_at.isoformat(),
    }


@router.delete("/copilot/{chat_id}")
def clear_chat_history(chat_id: str, db: Session = Depends(get_db)):
    """Clear conversation history for a chat session."""
    session = db.query(ChatSession).filter(ChatSession.session_id == chat_id).first()
    if session:
        session.messages_json = "[]"
        db.commit()
    return {"status": "cleared", "chat_id": chat_id}
