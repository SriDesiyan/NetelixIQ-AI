#!/usr/bin/env python3
"""
NetElixIQ AI — Hackathon Pipeline Script
=========================================
Reads CSVs from DATA_DIR, engineers features, loads a trained model from
MODEL_PATH, generates revenue forecasts, and writes predictions to OUTPUT_PATH.

Usage:
    python scripts/predict.py [DATA_DIR] [MODEL_PATH] [OUTPUT_PATH]

Defaults:
    DATA_DIR    = ./data
    MODEL_PATH  = ./pickle/model.pkl
    OUTPUT_PATH = ./output/predictions.csv

AIgnition 3.0 Hackathon — NetElixIQ AI
"""
import os
import sys
import logging
import pickle
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── Project root on path ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("netelixiq.predict")


# ── Column alias maps for dynamic schema detection ────────────────────────────
CHANNEL_ALIASES = {
    "google": {
        "date":        ["date", "day", "report date"],
        "campaign":    ["campaign", "campaign name"],
        "impressions": ["impressions", "impr."],
        "clicks":      ["clicks"],
        "spend":       ["cost", "spend", "amount spent", "cost (usd)"],
        "conversions": ["conversions", "all conv.", "all conversions"],
        "revenue":     ["conversion value", "conv. value", "all conv. value", "revenue"],
    },
    "meta": {
        "date":        ["date", "day", "reporting starts", "report start", "date start", "reporting start"],
        "campaign":    ["campaign name", "campaign", "ad set name", "adset name"],
        "impressions": ["impressions"],
        "clicks":      ["clicks (all)", "link clicks", "clicks"],
        "spend":       ["amount spent (usd)", "amount spent", "spend"],
        "conversions": ["purchases", "conversions", "results"],
        "revenue":     ["purchase conversion value", "revenue"],
    },
    "microsoft": {
        "date":        ["date", "gregorian date", "time period"],
        "campaign":    ["campaign name", "campaign"],
        "impressions": ["impressions"],
        "clicks":      ["clicks"],
        "spend":       ["spend", "revenue (usd)", "cost"],
        "conversions": ["conversions", "all conversions"],
        "revenue":     ["revenue", "all conversion revenue"],
    },
    "shopify": {
        "date":        ["date", "order date", "created at", "day"],
        "campaign":    ["source", "utm source", "marketing channel"],
        "impressions": ["sessions", "visits", "impressions"],
        "clicks":      ["clicks", "sessions"],
        "spend":       ["ad spend", "spend", "marketing spend"],
        "conversions": ["orders", "total orders", "conversions"],
        "revenue":     ["total sales", "net sales", "revenue", "gross revenue"],
    },
    "ga4": {
        "date":        ["date", "day"],
        "campaign":    ["campaign", "session campaign", "session default channel group"],
        "impressions": ["impressions", "screen page views"],
        "clicks":      ["clicks", "sessions"],
        "spend":       ["ad cost", "spend"],
        "conversions": ["conversions", "key events", "goal completions"],
        "revenue":     ["revenue", "total revenue", "purchase revenue"],
    },
}

UNIFIED_COLUMNS = ["date", "channel", "campaign", "impressions", "clicks", "spend", "conversions", "revenue"]

# ── Channel auto-detection heuristics ────────────────────────────────────────
CHANNEL_SIGNALS = {
    "google": ["cost", "conversion value", "impr.", "all conv."],
    "meta":   ["amount spent", "purchase conversion value", "clicks (all)"],
    "microsoft": ["gregorian date", "all conversion revenue"],
    "shopify": ["total sales", "net sales", "orders"],
    "ga4":    ["session default channel group", "total revenue", "key events"],
}


def detect_channel(df: pd.DataFrame, filename: str = "") -> str:
    """Auto-detect channel from column names and filename."""
    cols_lower = [c.strip().lower() for c in df.columns]
    fname_lower = filename.lower()

    # Filename hints
    for ch in ["google", "meta", "microsoft", "shopify", "ga4"]:
        if ch in fname_lower:
            return ch

    # Column signal matching
    scores = {}
    for ch, signals in CHANNEL_SIGNALS.items():
        scores[ch] = sum(1 for sig in signals if sig.lower() in cols_lower)

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        logger.info(f"  Auto-detected channel '{best}' (score={scores[best]}) from columns")
        return best

    return "google"  # safe default


def find_column(df_cols, aliases):
    """Find first matching column from aliases (case-insensitive)."""
    normalized = {c.strip().lower(): c for c in df_cols}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    return None


def parse_numeric(series: pd.Series) -> pd.Series:
    """Strip currency symbols and parse as float."""
    return (
        series.astype(str)
        .str.replace(r"[$,€£%]", "", regex=True)
        .str.strip()
        .replace({"": "0", "--": "0", "nan": "0"})
        .astype(float)
    )


def parse_csv(filepath: str) -> pd.DataFrame:
    """Parse a single CSV file into the unified schema."""
    filename = os.path.basename(filepath)
    logger.info(f"  Reading: {filename}")

    try:
        try:
            df = pd.read_csv(filepath, encoding="utf-8", thousands=",")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding="latin-1", thousands=",")
    except Exception as e:
        raise ValueError(f"Cannot read '{filename}': {e}")

    if df.empty:
        raise ValueError(f"'{filename}' is empty.")

    channel = detect_channel(df, filename)
    alias_map = CHANNEL_ALIASES.get(channel, {})

    # Rename columns
    rename = {}
    for target, aliases in alias_map.items():
        found = find_column(list(df.columns), aliases)
        if found:
            rename[found] = target

    df = df.rename(columns=rename)

    # Ensure all unified columns exist
    for col in UNIFIED_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0 if col not in ("date", "channel", "campaign") else ""

    df = df[UNIFIED_COLUMNS].copy()

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date"])

    # Parse numeric columns
    for col in ["impressions", "clicks", "spend", "conversions", "revenue"]:
        df[col] = parse_numeric(df[col])

    df["channel"] = channel

    # Derived metrics
    df["roas"] = np.where(df["spend"] > 0, df["revenue"] / df["spend"], 0.0)
    df["ctr"]  = np.where(df["impressions"] > 0, df["clicks"] / df["impressions"] * 100, 0.0)
    df["cvr"]  = np.where(df["clicks"] > 0, df["conversions"] / df["clicks"] * 100, 0.0)
    df["cpc"]  = np.where(df["clicks"] > 0, df["spend"] / df["clicks"], 0.0)

    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"    → {len(df)} rows | channel={channel} | spend={df['spend'].sum():.0f} | revenue={df['revenue'].sum():.0f}")
    return df


def load_all_csvs(data_dir: str) -> pd.DataFrame:
    """Read all CSVs from data_dir recursively."""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"DATA_DIR not found: {data_dir}")

    csv_files = list(data_path.rglob("*.csv")) + list(data_path.rglob("*.CSV"))
    # Deduplicate paths (handles case-insensitive filesystems)
    csv_files = list({f.resolve(): f for f in csv_files}.values())
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")

    logger.info(f"Found {len(csv_files)} CSV file(s) in '{data_dir}'")

    dfs = []
    errors = []
    for f in sorted(csv_files):
        try:
            dfs.append(parse_csv(str(f)))
        except Exception as e:
            logger.warning(f"  Skipping {f.name}: {e}")
            errors.append(str(e))

    if not dfs:
        raise ValueError(f"All CSV files failed to parse: {'; '.join(errors)}")

    combined = pd.concat(dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
    logger.info(f"Combined dataset: {len(combined)} rows across {combined['channel'].nunique()} channel(s)")
    return combined


def build_features(df: pd.DataFrame, target_col: str = "revenue") -> pd.DataFrame:
    """Engineer time-series features for the ML model."""
    from backend.services.forecasting.feature_eng import (
        build_daily_aggregates,
        build_feature_matrix,
        prepare_forecast_input,
    )

    daily = build_daily_aggregates(df)
    logger.info(f"Daily aggregates: {len(daily)} days")
    return daily


def load_model(model_path: str):
    """Load the pickled forecasting pipeline."""
    from backend.services.forecasting.pipeline import ForecastingPipeline
    logger.info(f"Loading model from: {model_path}")
    pipeline = ForecastingPipeline.load(model_path)
    return pipeline


def update_pipeline_data(pipeline, df: pd.DataFrame):
    """Update pipeline's daily_df with new data and re-fit prophet ONLY if new data is detected."""
    from backend.services.forecasting.feature_eng import build_daily_aggregates
    from backend.services.forecasting.prophet_model import ProphetForecaster

    new_daily = build_daily_aggregates(df)

    if pipeline.daily_df is not None:
        old_dates = set(pipeline.daily_df["date"].astype(str))
        new_dates = set(new_daily["date"].astype(str))
        if len(new_dates - old_dates) > 0:
            logger.info(f"  New data detected ({len(new_dates - old_dates)} new days) — updating pipeline and re-fitting Prophet")
            pipeline.daily_df = new_daily
            try:
                pipeline.prophet = ProphetForecaster(target_col=pipeline.target_col)
                pipeline.prophet.fit(pipeline.daily_df)
            except Exception as e:
                logger.warning(f"  Prophet fitting failed on new data: {e}")
        else:
            logger.info("  Data matches training set — utilizing pre-serialized models (no runtime fitting)")
    else:
        pipeline.daily_df = new_daily
        try:
            pipeline.prophet = ProphetForecaster(target_col=pipeline.target_col)
            pipeline.prophet.fit(pipeline.daily_df)
        except Exception as e:
            logger.warning(f"  Prophet fitting failed on empty pipeline: {e}")


def generate_predictions(pipeline, horizons=(30, 60, 90)) -> pd.DataFrame:
    """Generate forecasts for multiple horizons and return as flat DataFrame."""
    all_rows = []

    for horizon in horizons:
        logger.info(f"  Generating {horizon}-day forecast...")
        try:
            result = pipeline.predict(horizon=horizon)
            forecast = result.get("forecast", [])
            summary = result.get("summary", {})
            confidence = result.get("confidence", 0.0)
            model_weights = result.get("model_weights", {})

            for row in forecast:
                all_rows.append({
                    "horizon_days":      horizon,
                    "date":              row["date"],
                    "revenue_p10":       row["p10"],
                    "revenue_p50":       row["p50"],
                    "revenue_p90":       row["p90"],
                    "confidence":        round(confidence, 4),
                    "lgbm_weight":       round(model_weights.get("lgbm", 0.6), 4),
                    "prophet_weight":    round(model_weights.get("prophet", 0.4), 4),
                    "total_p10":         summary.get("total_p10", 0),
                    "total_p50":         summary.get("total_p50", 0),
                    "total_p90":         summary.get("total_p90", 0),
                    "model_mape":        round(pipeline.mape, 4),
                    "generated_at":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
        except Exception as e:
            logger.error(f"  Forecast failed for horizon={horizon}: {e}")

    if not all_rows:
        raise RuntimeError("No predictions generated for any horizon.")

    return pd.DataFrame(all_rows)


def write_output(df: pd.DataFrame, output_path: str) -> None:
    """Write predictions DataFrame to CSV."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    logger.info(f"Predictions written to: {output_path} ({len(df)} rows)")


def main():
    parser = argparse.ArgumentParser(
        description="NetElixIQ AI — Generate revenue forecasts from marketing CSVs"
    )
    parser.add_argument("data_dir",    nargs="?", default="./data",
                        help="Directory containing marketing CSV files (default: ./data)")
    parser.add_argument("model_path",  nargs="?", default="./pickle/model.pkl",
                        help="Path to the trained model pickle (default: ./pickle/model.pkl)")
    parser.add_argument("output_path", nargs="?", default="./output/predictions.csv",
                        help="Output CSV path for predictions (default: ./output/predictions.csv)")
    parser.add_argument("--horizons",  default="30,60,90",
                        help="Comma-separated forecast horizons in days (default: 30,60,90)")

    args = parser.parse_args()
    horizons = [int(h.strip()) for h in args.horizons.split(",")]

    logger.info("=" * 60)
    logger.info("  NetElixIQ AI — Hackathon Prediction Pipeline")
    logger.info("=" * 60)
    logger.info(f"  DATA_DIR    = {args.data_dir}")
    logger.info(f"  MODEL_PATH  = {args.model_path}")
    logger.info(f"  OUTPUT_PATH = {args.output_path}")
    logger.info(f"  HORIZONS    = {horizons}")
    logger.info("=" * 60)

    # Step 1: Load CSV data
    logger.info("[1/4] Loading CSV data...")
    df = load_all_csvs(args.data_dir)

    if len(df) < 10:
        logger.error(f"Insufficient data: only {len(df)} rows. Need at least 10.")
        sys.exit(1)

    # Step 2: Load model
    logger.info("[2/4] Loading trained model...")
    pipeline = load_model(args.model_path)

    # Step 3: Update pipeline with new data, regenerate features
    logger.info("[3/4] Engineering features & updating pipeline...")
    update_pipeline_data(pipeline, df)

    # Step 4: Generate predictions
    logger.info("[4/4] Generating predictions...")
    predictions = generate_predictions(pipeline, horizons=horizons)

    # Step 5: Write output
    write_output(predictions, args.output_path)

    # Summary
    logger.info("=" * 60)
    logger.info("  PREDICTION SUMMARY")
    logger.info("=" * 60)
    for h in horizons:
        h_rows = predictions[predictions["horizon_days"] == h]
        if not h_rows.empty:
            p50 = h_rows["total_p50"].iloc[0]
            p10 = h_rows["total_p10"].iloc[0]
            p90 = h_rows["total_p90"].iloc[0]
            conf = h_rows["confidence"].iloc[0]
            logger.info(f"  {h:2d}-day Revenue Forecast:")
            logger.info(f"       P50: ${p50:>12,.0f}")
            logger.info(f"       P10: ${p10:>12,.0f}")
            logger.info(f"       P90: ${p90:>12,.0f}")
            logger.info(f"       Confidence: {conf:.1%}")
    logger.info("=" * 60)
    logger.info(f"  Output: {args.output_path}")
    logger.info("  Status: SUCCESS")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
