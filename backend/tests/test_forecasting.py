"""
NetElixIQ AI — Test: Forecasting Pipeline
Tests fitting, forecasting, conformal prediction intervals, and serialization.
"""
import os
import sys
import tempfile
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.forecasting.pipeline import ForecastingPipeline


@pytest.fixture
def sample_marketing_data():
    """Generate 60 days of daily campaign data across channels."""
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=60)
    data = []
    for dt in dates:
        for ch in ["google", "meta"]:
            spend = np.random.uniform(100, 500)
            roas = np.random.uniform(2.5, 4.0)
            revenue = spend * roas
            data.append({
                "date": dt.strftime("%Y-%m-%d"),
                "channel": ch,
                "campaign": "Test Campaign",
                "spend": spend,
                "revenue": revenue,
                "impressions": spend * 1000,
                "clicks": spend * 10,
                "conversions": spend * 0.2,
            })
    return pd.DataFrame(data)


def test_pipeline_fit_predict(sample_marketing_data):
    # Initialize pipeline
    pipeline = ForecastingPipeline()
    assert not pipeline.is_fitted

    # Fit the pipeline
    pipeline.fit(sample_marketing_data, target_col="revenue")
    assert pipeline.is_fitted
    assert pipeline.daily_df is not None
    assert pipeline.training_stats.get("rows_used", 0) == 60

    # Predict
    horizon = 14
    result = pipeline.predict(horizon=horizon)
    
    # Verify result structure
    assert "forecast" in result
    assert "summary" in result
    assert "confidence" in result
    assert "training_stats" in result

    forecast = result["forecast"]
    assert len(forecast) == horizon
    for row in forecast:
        assert "date" in row
        assert "p10" in row
        assert "p50" in row
        assert "p90" in row
        # P10 <= P50 <= P90
        assert row["p10"] <= row["p50"]
        assert row["p50"] <= row["p90"]

    summary = result["summary"]
    assert "total_p10" in summary
    assert "total_p50" in summary
    assert "total_p90" in summary
    assert summary["total_p10"] <= summary["total_p50"] <= summary["total_p90"]


def test_pipeline_serialization(sample_marketing_data):
    # Create temp directory for artifact
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "test_model.pkl")
        
        # Fit and save
        pipeline = ForecastingPipeline(model_artifact_path=model_path)
        pipeline.fit(sample_marketing_data, target_col="revenue")
        pipeline.save(model_path)
        
        assert os.path.exists(model_path)

        # Load back using standard classmethod loader
        loaded_pipeline = ForecastingPipeline.load(model_path)
        
        assert loaded_pipeline.is_fitted
        assert loaded_pipeline.mape == pipeline.mape
        assert loaded_pipeline.model_weights == pipeline.model_weights

        # Predict with loaded pipeline
        res = loaded_pipeline.predict(horizon=7)
        assert len(res["forecast"]) == 7
