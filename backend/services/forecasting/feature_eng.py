"""
NetElixIQ AI — Feature Engineering
Transforms normalized campaign data into ML-ready time-series features.
Adapted from Sales-For time-series patterns and consultantOS feature pipelines.
"""
import logging
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def build_daily_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate multi-channel, multi-campaign data to daily totals.

    Args:
        df: Normalized campaign DataFrame with date, channel, spend, revenue, etc.

    Returns:
        Daily aggregated DataFrame with one row per date.
    """
    numeric_cols = ["impressions", "clicks", "spend", "conversions", "revenue"]

    # Aggregate by date across all channels
    agg = df.groupby("date")[
        [c for c in numeric_cols if c in df.columns]
    ].sum().reset_index()

    # Sort by date
    agg["date"] = pd.to_datetime(agg["date"])
    agg = agg.sort_values("date").reset_index(drop=True)

    # Compute derived metrics on aggregated data
    agg["roas"] = np.where(agg["spend"] > 0, agg["revenue"] / agg["spend"], 0.0)
    agg["ctr"] = np.where(
        agg["impressions"] > 0, agg["clicks"] / agg["impressions"] * 100, 0.0
    )
    agg["cvr"] = np.where(
        agg["clicks"] > 0, agg["conversions"] / agg["clicks"] * 100, 0.0
    )
    agg["cpc"] = np.where(agg["clicks"] > 0, agg["spend"] / agg["clicks"], 0.0)

    logger.info(f"Daily aggregates: {len(agg)} days, spend={agg['spend'].sum():.0f}")
    return agg


def build_channel_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by date + channel."""
    numeric_cols = ["impressions", "clicks", "spend", "conversions", "revenue"]
    agg = df.groupby(["date", "channel"])[
        [c for c in numeric_cols if c in df.columns]
    ].sum().reset_index()
    agg["date"] = pd.to_datetime(agg["date"])
    agg["roas"] = np.where(agg["spend"] > 0, agg["revenue"] / agg["spend"], 0.0)
    return agg.sort_values(["date", "channel"]).reset_index(drop=True)


def add_time_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Add calendar/temporal features to a daily DataFrame.
    Features include day-of-week, month, quarter, week-of-year, and cyclic encodings.
    """
    df = df.copy()
    dt = pd.to_datetime(df[date_col])

    df["day_of_week"] = dt.dt.dayofweek          # 0=Mon, 6=Sun
    df["day_of_month"] = dt.dt.day
    df["week_of_year"] = dt.dt.isocalendar().week.astype(int)
    df["month"] = dt.dt.month
    df["quarter"] = dt.dt.quarter
    df["year"] = dt.dt.year
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
    df["day_index"] = (dt - dt.min()).dt.days      # Linear trend feature

    # Cyclic encodings for periodic features
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


def add_lag_features(
    df: pd.DataFrame,
    target_col: str = "revenue",
    lags: List[int] = [1, 2, 3, 7, 14, 28],
) -> pd.DataFrame:
    """
    Add lag features for the target column.
    Ensures no data leakage — lags are always past values.
    """
    df = df.copy()
    for lag in lags:
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)
    return df


def add_rolling_features(
    df: pd.DataFrame,
    target_col: str = "revenue",
    windows: List[int] = [7, 14, 28],
) -> pd.DataFrame:
    """Add rolling mean and std features for the target column."""
    df = df.copy()
    for window in windows:
        df[f"{target_col}_roll_mean_{window}"] = (
            df[target_col].shift(1).rolling(window=window, min_periods=1).mean()
        )
        df[f"{target_col}_roll_std_{window}"] = (
            df[target_col].shift(1).rolling(window=window, min_periods=1).std().fillna(0)
        )
    return df


def add_spend_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add spend-related predictive features."""
    df = df.copy()

    if "spend" in df.columns:
        for lag in [1, 7]:
            df[f"spend_lag_{lag}"] = df["spend"].shift(lag)
        for window in [7, 14]:
            df[f"spend_roll_mean_{window}"] = (
                df["spend"].shift(1).rolling(window=window, min_periods=1).mean()
            )
        df["spend_change_pct"] = df["spend"].pct_change().fillna(0).clip(-2, 2)

    if "roas" in df.columns:
        for lag in [1, 7]:
            df[f"roas_lag_{lag}"] = df["roas"].shift(lag)

    return df


def build_feature_matrix(
    df: pd.DataFrame,
    target_col: str = "revenue",
    drop_na: bool = True,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build complete feature matrix for ML training.

    Args:
        df: Daily aggregated DataFrame.
        target_col: The target metric to predict.
        drop_na: Whether to drop rows with NaN features.

    Returns:
        (X, y) tuple for ML training.
    """
    df = df.copy()
    df = add_time_features(df)
    df = add_lag_features(df, target_col=target_col)
    df = add_rolling_features(df, target_col=target_col)
    df = add_spend_features(df)

    if drop_na:
        df = df.dropna().reset_index(drop=True)

    feature_cols = [c for c in df.columns if c not in [
        "date", target_col, "channel", "campaign"
    ] and not c.endswith("_raw")]

    y = df[target_col]
    X = df[feature_cols]

    logger.info(f"Feature matrix: {X.shape} | target={target_col} | mean={y.mean():.2f}")
    return X, y


def prepare_forecast_input(
    df: pd.DataFrame,
    horizon: int,
    target_col: str = "revenue",
) -> pd.DataFrame:
    """
    Prepare input features for forecasting future dates.
    Extends the historical dataframe with future date rows and fills features.

    Args:
        df: Historical daily aggregated DataFrame.
        horizon: Number of days to forecast.
        target_col: Target column name.

    Returns:
        DataFrame with future rows ready for prediction (lag features filled from history).
    """
    df = df.copy()
    last_date = pd.to_datetime(df["date"].max())

    # Create future date rows
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )
    future_df = pd.DataFrame({"date": future_dates})

    # Carry forward last-known spend (can be overridden by budget simulation)
    if "spend" in df.columns:
        last_spend = df["spend"].iloc[-7:].mean()
        future_df["spend"] = last_spend

    for col in ["impressions", "clicks", "conversions", "roas", "ctr", "cvr", "cpc"]:
        if col in df.columns:
            future_df[col] = df[col].iloc[-7:].mean()

    # Set target to NaN for future rows
    future_df[target_col] = np.nan

    combined = pd.concat([df, future_df], ignore_index=True)
    combined = add_time_features(combined)
    combined = add_lag_features(combined, target_col=target_col)
    combined = add_rolling_features(combined, target_col=target_col)
    combined = add_spend_features(combined)

    # Return only future rows
    future_out = combined.iloc[-horizon:].copy()
    return future_out
