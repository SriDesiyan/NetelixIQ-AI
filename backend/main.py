"""
NetElixIQ AI — FastAPI Application Entry Point
Marketing Decision Intelligence Platform
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db
from backend.utils.logging import setup_logging
from backend.api import health, ingest, forecast, simulate, analyst, copilot, reports

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("NetElixIQ AI starting up...")
    init_db()

    # Generate demo data if it doesn't exist and demo mode is on
    if settings.demo_mode:
        sample_dir = settings.demo_data_dir
        google_sample = os.path.join(sample_dir, "google_ads_sample.csv")
        if not os.path.exists(google_sample):
            logger.info("Demo mode: generating sample data...")
            try:
                import subprocess
                subprocess.run(
                    [sys.executable, "scripts/generate_demo_data.py"],
                    check=True, timeout=30
                )
            except Exception as e:
                logger.warning(f"Demo data generation failed: {e}")

    logger.info(f"NetElixIQ AI started — http://{settings.host}:{settings.port}")
    logger.info(f"  API Docs:   http://{settings.host}:{settings.port}/api/docs")
    logger.info(f"  Demo Mode:  {settings.demo_mode}")
    logger.info(
        f"  Gemini:     {'Configured' if settings.gemini_api_key and 'placeholder' not in (settings.gemini_api_key or '') else 'Demo Mode'}"
    )

    yield  # Application is running

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("NetElixIQ AI shutting down.")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NetElixIQ AI",
    description="""
## 🚀 NetElixIQ AI — Marketing Decision Intelligence Platform

**Predict. Simulate. Optimize.**

AI-powered platform for ecommerce marketing intelligence built for the AIgnition 3.0 hackathon.

### Features
- **Data Ingestion**: Google Ads, Meta Ads, Microsoft Ads, Shopify, GA4 CSV import
- **Forecasting Engine**: Prophet + LightGBM + Quantile + Conformal ensemble (P10/P50/P90)
- **Budget Simulation**: Monte Carlo simulation of 2,000 budget allocation scenarios
- **AI Business Analyst**: Gemini-powered forecast explanations and recommendations
- **Marketing Copilot**: Natural language Q&A about your campaign data
- **Executive Dashboard**: Interactive KPI dashboard with risk scoring
""",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health.router,   prefix="/api", tags=["Health"])
app.include_router(ingest.router,   prefix="/api", tags=["Data Ingestion"])
app.include_router(forecast.router, prefix="/api", tags=["Forecasting"])
app.include_router(simulate.router, prefix="/api", tags=["Budget Simulation"])
app.include_router(analyst.router,  prefix="/api", tags=["AI Analyst"])
app.include_router(copilot.router,  prefix="/api", tags=["Marketing Copilot"])
app.include_router(reports.router,  prefix="/api", tags=["Reports"])


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
