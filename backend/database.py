"""
NetElixIQ AI — Database Setup
SQLAlchemy with SQLite default, PostgreSQL-ready.
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.config import settings

# ── Engine & Session ──────────────────────────────────────────────────────────
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # Disable SQL echo in production
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base (modern declarative API — replaces deprecated declarative_base()) ────
class Base(DeclarativeBase):
    pass


# ── ORM Models ────────────────────────────────────────────────────────────────

class CampaignRecord(Base):
    """Normalized campaign performance record from any channel."""
    __tablename__ = "campaign_records"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    upload_session_id = Column(String(64), index=True, nullable=False)
    date             = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    channel          = Column(String(50), nullable=False, index=True)  # google | meta | microsoft | shopify | ga4
    campaign         = Column(String(255), nullable=True)
    impressions      = Column(Float, default=0.0)
    clicks           = Column(Float, default=0.0)
    spend            = Column(Float, default=0.0)
    conversions      = Column(Float, default=0.0)
    revenue          = Column(Float, default=0.0)
    roas             = Column(Float, default=0.0)
    ctr              = Column(Float, default=0.0)
    cvr              = Column(Float, default=0.0)
    cpc              = Column(Float, default=0.0)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ForecastResult(Base):
    """Stored forecast output with confidence intervals."""
    __tablename__ = "forecast_results"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    session_id    = Column(String(64), index=True, nullable=False)
    horizon_days  = Column(Integer, nullable=False)  # 30 | 60 | 90
    metric        = Column(String(50), nullable=False)  # revenue | roas | channel_contribution
    forecast_json = Column(Text, nullable=False)  # JSON array of {date, p10, p50, p90}
    model_weights = Column(JSON, nullable=True)
    mape          = Column(Float, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SimulationResult(Base):
    """Budget simulation result."""
    __tablename__ = "simulation_results"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    session_id           = Column(String(64), index=True, nullable=False)
    google_budget        = Column(Float, nullable=False)
    meta_budget          = Column(Float, nullable=False)
    microsoft_budget     = Column(Float, nullable=False)
    expected_revenue_p50 = Column(Float)
    expected_roas_p50    = Column(Float)
    channel_mix_json     = Column(JSON)
    confidence           = Column(Float)
    simulation_json      = Column(Text)
    created_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatSession(Base):
    """Marketing Copilot conversation session."""
    __tablename__ = "chat_sessions"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    session_id    = Column(String(64), unique=True, index=True, nullable=False)
    messages_json = Column(Text, default="[]")  # JSON array of {role, content}
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ── Dependency Injection ──────────────────────────────────────────────────────

def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
