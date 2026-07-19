"""
NetElixIQ AI — Test: API endpoints
Tests routers using FastAPI TestClient.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.main import app
from backend.config import settings

# Force demo mode and a temporary database during tests
settings.demo_mode = True
settings.database_url = "sqlite:///:memory:"

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "version" in response.json()


def test_ingest_demo_data():
    response = client.post("/api/ingest/demo")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["total_rows"] > 0
    assert "channels" in data


def test_get_session_summary():
    # Load demo data first to get a session
    demo_res = client.post("/api/ingest/demo")
    session_id = demo_res.json()["session_id"]

    response = client.get(f"/api/ingest/sessions/{session_id}/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["session_id"] == session_id
    assert "total_spend" in summary
    assert "total_revenue" in summary


def test_generate_forecast():
    # Load demo data
    demo_res = client.post("/api/ingest/demo")
    session_id = demo_res.json()["session_id"]

    # Forecast endpoint
    response = client.post(f"/api/forecast/{session_id}?horizon=7&metric=revenue")
    assert response.status_code == 200
    forecast_data = response.json()
    assert "forecast" in forecast_data
    assert len(forecast_data["forecast"]) == 7
    assert "summary" in forecast_data


def test_budget_simulation():
    # Load demo data to get a valid session_id
    demo_res = client.post("/api/ingest/demo")
    session_id = demo_res.json()["session_id"]

    payload = {
        "session_id": session_id,
        "google_budget": 5000.0,
        "meta_budget": 3000.0,
        "microsoft_budget": 1000.0,
        "horizon_days": 30
    }
    response = client.post("/api/simulate/budget", json=payload)
    assert response.status_code == 200
    sim = response.json()
    assert "revenue" in sim
    assert "roas" in sim
    assert "p50" in sim["revenue"]


def test_analyst_insights():
    demo_res = client.post("/api/ingest/demo")
    session_id = demo_res.json()["session_id"]

    # Test risk analysis
    response = client.get(f"/api/analyst/{session_id}/risk?horizon=7")
    assert response.status_code == 200
    risk = response.json()
    assert "risk_score" in risk
    assert "risk_level" in risk
    assert "explanation" in risk
