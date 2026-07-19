"""
NetElixIQ AI — train_model.py
Pre-trains the forecasting pipeline on demo data and saves a pickle artifact.
Run once before starting the backend for faster cold-start.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    import pandas as pd
    from backend.services.ingestion.parsers import parse_multiple_channels
    from backend.services.forecasting.pipeline import ForecastingPipeline
    from backend.services.simulation.budget_sim import BudgetSimulator

    DATA_DIR = "data/sample"
    MODEL_OUT = "pickle/pipeline_demo.pkl"
    MODEL_OUT_HACKATHON = "pickle/model.pkl"

    # --- Load sample CSVs ---
    channel_map = {
        "google_ads_sample.csv": "google",
        "meta_ads_sample.csv": "meta",
        "microsoft_ads_sample.csv": "microsoft",
        "shopify_sample.csv": "shopify",
        "ga4_sample.csv": "ga4",
    }

    file_specs = []
    for filename, channel in channel_map.items():
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                file_specs.append({"content": f.read(), "channel": channel, "filename": filename})
        else:
            logger.warning(f"Demo file not found: {filepath}")

    if not file_specs:
        logger.error("No demo data found. Run: python scripts/generate_demo_data.py first")
        sys.exit(1)

    logger.info(f"Loaded {len(file_specs)} channel files")
    df = parse_multiple_channels(file_specs)
    logger.info(f"Parsed {len(df)} rows across channels: {df['channel'].unique().tolist()}")

    # --- Train forecasting pipeline ---
    os.makedirs("pickle", exist_ok=True)
    logger.info("Training forecasting pipeline (this may take 30-60 seconds)...")

    pipeline = ForecastingPipeline(model_artifact_path=MODEL_OUT)
    pipeline.fit(df, target_col="revenue")
    pipeline.save(MODEL_OUT)
    pipeline.save(MODEL_OUT_HACKATHON)

    logger.info(f"[OK] Pipeline saved to {MODEL_OUT} and {MODEL_OUT_HACKATHON}")
    logger.info(f"     MAPE: {pipeline.mape:.3f}")
    logger.info(f"     Weights: {pipeline.model_weights}")
    logger.info(f"     Training rows: {pipeline.training_stats.get('training_rows', 0)}")

    # --- Quick prediction test ---
    result = pipeline.predict(horizon=30)
    p50_total = result["summary"]["total_p50"]
    confidence = result["confidence"]
    logger.info(f"     30-day P50 forecast: ${p50_total:,.0f}")
    logger.info(f"     Confidence: {confidence:.1%}")

    # --- Calibrate budget simulator ---
    logger.info("Calibrating budget simulator...")
    sim = BudgetSimulator()
    sim.calibrate_from_data(df)
    test_sim = sim.simulate(google_budget=15000, meta_budget=8000, microsoft_budget=3000)
    sim_rev = test_sim["revenue"]["p50"]
    logger.info(f"     Budget sim test: ${sim_rev:,.0f} P50 revenue (30d)")

    print("\n[DONE] Model training complete!")
    print(f"  Pipeline: {MODEL_OUT}")
    print(f"  MAPE: {pipeline.mape:.1%}")
    print(f"  30d Revenue Forecast: ${p50_total:,.0f}")
    print(f"  Confidence: {confidence:.0%}")
    print("\nThe backend will auto-load this model on startup.")


if __name__ == "__main__":
    main()
