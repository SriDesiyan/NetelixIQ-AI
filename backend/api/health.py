"""
NetElixIQ AI — Health Check API
"""
import platform
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    environment: str
    gemini_configured: bool
    demo_mode: bool
    python_version: str


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return HealthResponse(
        status="healthy",
        service="NetElixIQ AI — Marketing Decision Intelligence Platform",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        environment=settings.environment,
        gemini_configured=(
            bool(settings.gemini_api_key)
            and "placeholder" not in (settings.gemini_api_key or "")
        ),
        demo_mode=settings.demo_mode,
        python_version=platform.python_version(),
    )


@router.get("/")
def root():
    """Root redirect to API docs."""
    return {
        "message": "NetElixIQ AI — Predict. Simulate. Optimize.",
        "docs": "/api/docs",
        "health": "/api/health",
        "version": settings.app_version,
    }
