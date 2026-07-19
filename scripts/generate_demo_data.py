#!/usr/bin/env python3
"""
NetElixIQ AI — Demo Data Generator
Generates realistic synthetic marketing data for all 5 channels (90 days).
Designed to showcase forecasting, budget simulation, and AI analyst features
without requiring real ad account access.

Run: python scripts/generate_demo_data.py
"""
import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Configuration ─────────────────────────────────────────────────────────────
DAYS = 120  # 120 days of history
START_DATE = date.today() - timedelta(days=DAYS)
OUTPUT_DIR = "data/sample"
SEED = 42

np.random.seed(SEED)
random.seed(SEED)

# ── Channel Profiles ──────────────────────────────────────────────────────────
# Each channel has realistic spend levels, ROAS ranges, and seasonal patterns
CHANNEL_PROFILES = {
    "google": {
        "daily_spend_mean": 420,
        "daily_spend_std": 80,
        "base_roas": 3.8,
        "roas_volatility": 0.4,
        "campaigns": [
            "Brand Search",
            "Non-Brand Search",
            "Shopping - Electronics",
            "Display Remarketing",
        ],
    },
    "meta": {
        "daily_spend_mean": 280,
        "daily_spend_std": 60,
        "base_roas": 2.9,
        "roas_volatility": 0.6,
        "campaigns": [
            "Prospecting - Lookalike",
            "Retargeting - 30d",
            "Video Awareness",
            "Catalog Sales",
        ],
    },
    "microsoft": {
        "daily_spend_mean": 95,
        "daily_spend_std": 25,
        "base_roas": 3.2,
        "roas_volatility": 0.3,
        "campaigns": [
            "Brand Keywords",
            "Competitor Targeting",
        ],
    },
    "shopify": {
        "daily_spend_mean": 0,  # Shopify is revenue data, spend from ads
        "campaigns": ["Organic", "Email", "Referral", "Social"],
    },
    "ga4": {
        "daily_spend_mean": 0,
        "campaigns": [
            "google / cpc",
            "facebook / cpc",
            "organic / none",
            "email / newsletter",
        ],
    },
}

# Weekday multipliers (Mon=0 .. Sun=6)
WEEKDAY_MULTIPLIER = [1.0, 1.05, 1.1, 1.08, 1.15, 0.85, 0.75]

# Seasonal multiplier by month (Jan=0..Dec=11) — Q4 peak
MONTH_MULTIPLIER = [0.8, 0.85, 0.9, 0.95, 1.0, 1.0, 0.95, 0.95, 1.0, 1.05, 1.2, 1.35]


def _seasonal_factor(dt: date) -> float:
    """Combined weekday + monthly seasonality multiplier."""
    return WEEKDAY_MULTIPLIER[dt.weekday()] * MONTH_MULTIPLIER[dt.month - 1]


def _trend_factor(day_index: int, total_days: int) -> float:
    """Gentle upward trend over the period (0% to 15%)."""
    return 1.0 + 0.15 * (day_index / total_days)


def generate_google_ads() -> pd.DataFrame:
    """Generate Google Ads CSV data."""
    rows = []
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    for i, dt in enumerate(dates):
        sf = _seasonal_factor(dt)
        tf = _trend_factor(i, DAYS)

        for campaign in CHANNEL_PROFILES["google"]["campaigns"]:
            profile = CHANNEL_PROFILES["google"]
            spend = max(0, np.random.normal(
                profile["daily_spend_mean"] / 4 * sf * tf,
                profile["daily_spend_std"] / 4
            ))
            roas = max(0.5, np.random.normal(profile["base_roas"], profile["roas_volatility"]))
            revenue = spend * roas
            impressions = spend * np.random.uniform(800, 1200)
            clicks = impressions * np.random.uniform(0.02, 0.06)
            conversions = clicks * np.random.uniform(0.03, 0.08)

            rows.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Campaign": campaign,
                "Impressions": round(impressions),
                "Clicks": round(clicks),
                "Cost": round(spend, 2),
                "Conversions": round(conversions, 1),
                "Conversion value": round(revenue, 2),
            })

    return pd.DataFrame(rows)


def generate_meta_ads() -> pd.DataFrame:
    """Generate Meta Ads CSV data."""
    rows = []
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    for i, dt in enumerate(dates):
        sf = _seasonal_factor(dt)
        tf = _trend_factor(i, DAYS)

        # Meta ROAS declining trend in last 30 days (interesting for AI analyst)
        roas_penalty = 1.0 if i < DAYS - 30 else max(0.6, 1.0 - (i - (DAYS - 30)) * 0.015)

        for campaign in CHANNEL_PROFILES["meta"]["campaigns"]:
            profile = CHANNEL_PROFILES["meta"]
            spend = max(0, np.random.normal(
                profile["daily_spend_mean"] / 4 * sf * tf,
                profile["daily_spend_std"] / 4
            ))
            roas = max(0.3, np.random.normal(
                profile["base_roas"] * roas_penalty, profile["roas_volatility"]
            ))
            revenue = spend * roas
            impressions = spend * np.random.uniform(2500, 4000)
            clicks = impressions * np.random.uniform(0.008, 0.025)
            purchases = clicks * np.random.uniform(0.02, 0.06)

            rows.append({
                "Day": dt.strftime("%Y-%m-%d"),
                "Campaign name": campaign,
                "Impressions": round(impressions),
                "Clicks (all)": round(clicks),
                "Amount spent (USD)": round(spend, 2),
                "Purchases": round(purchases, 1),
                "Purchase conversion value": round(revenue, 2),
            })

    return pd.DataFrame(rows)


def generate_microsoft_ads() -> pd.DataFrame:
    """Generate Microsoft Ads CSV data."""
    rows = []
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    for i, dt in enumerate(dates):
        sf = _seasonal_factor(dt)
        tf = _trend_factor(i, DAYS)

        for campaign in CHANNEL_PROFILES["microsoft"]["campaigns"]:
            profile = CHANNEL_PROFILES["microsoft"]
            spend = max(0, np.random.normal(
                profile["daily_spend_mean"] / 2 * sf * tf,
                profile["daily_spend_std"] / 2
            ))
            roas = max(0.8, np.random.normal(profile["base_roas"], profile["roas_volatility"]))
            revenue = spend * roas
            impressions = spend * np.random.uniform(600, 900)
            clicks = impressions * np.random.uniform(0.03, 0.07)
            conversions = clicks * np.random.uniform(0.04, 0.09)

            rows.append({
                "Gregorian date": dt.strftime("%Y-%m-%d"),
                "Campaign name": campaign,
                "Impressions": round(impressions),
                "Clicks": round(clicks),
                "Spend": round(spend, 2),
                "Conversions": round(conversions, 1),
                "Revenue": round(revenue, 2),
            })

    return pd.DataFrame(rows)


def generate_shopify() -> pd.DataFrame:
    """Generate Shopify daily revenue data."""
    rows = []
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    total_ad_spend_by_date = {}  # Will be used for context
    for i, dt in enumerate(dates):
        sf = _seasonal_factor(dt)
        tf = _trend_factor(i, DAYS)
        base_revenue = 1400 * sf * tf

        for source in CHANNEL_PROFILES["shopify"]["campaigns"]:
            source_mult = {"Organic": 0.3, "Email": 0.2, "Referral": 0.15, "Social": 0.35}
            revenue = max(0, np.random.normal(
                base_revenue * source_mult[source],
                base_revenue * source_mult[source] * 0.2
            ))
            orders = revenue / np.random.uniform(55, 120)
            sessions = orders / np.random.uniform(0.02, 0.05)

            rows.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Source": source,
                "Sessions": round(sessions),
                "Orders": round(orders, 1),
                "Total sales": round(revenue, 2),
                "Ad spend": 0.0,
            })

    return pd.DataFrame(rows)


def generate_ga4() -> pd.DataFrame:
    """Generate GA4 export data."""
    rows = []
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    for i, dt in enumerate(dates):
        sf = _seasonal_factor(dt)
        tf = _trend_factor(i, DAYS)

        for channel in CHANNEL_PROFILES["ga4"]["campaigns"]:
            sessions = max(1, int(np.random.normal(500 * sf * tf, 100)))
            revenue = sessions * np.random.uniform(0.5, 3.5)
            conversions = sessions * np.random.uniform(0.02, 0.06)

            rows.append({
                "Date": dt.strftime("%Y-%m-%d"),
                "Session default channel group": channel,
                "Sessions": sessions,
                "Conversions": round(conversions, 1),
                "Total revenue": round(revenue, 2),
            })

    return pd.DataFrame(rows)


def main():
    """Generate all sample data files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[*] Generating demo data for NetElixIQ AI...")
    print(f"   Period: {START_DATE} to {date.today()} ({DAYS} days)")

    generators = {
        "google_ads_sample.csv": generate_google_ads,
        "meta_ads_sample.csv": generate_meta_ads,
        "microsoft_ads_sample.csv": generate_microsoft_ads,
        "shopify_sample.csv": generate_shopify,
        "ga4_sample.csv": generate_ga4,
    }

    for filename, generator in generators.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        df = generator()
        df.to_csv(filepath, index=False)
        print(f"   [OK] {filename}: {len(df)} rows")

    print(f"\n[DONE] Demo data generated in '{OUTPUT_DIR}/'")
    print("   Load it via the dashboard or run train_model.py to pre-train the forecast model.")


if __name__ == "__main__":
    main()
