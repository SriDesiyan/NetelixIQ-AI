"""
NetElixIQ AI — Data Validation
Validates ingested marketing data for quality, consistency, and completeness.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation with issues and statistics."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "stats": self.stats,
        }


class DataValidator:
    """
    Multi-layer validator for marketing campaign data.
    Checks schema consistency, missing values, date ranges, and campaign integrity.
    """

    MIN_ROWS = 7  # At least 1 week of data
    MAX_GAP_DAYS = 14  # Alert on gaps larger than 2 weeks
    NEGATIVE_ALLOWED_COLS = []  # No negatives expected in marketing data

    def validate(self, df: pd.DataFrame, channel: str = "unknown") -> ValidationResult:
        """
        Run all validation checks on a normalized DataFrame.

        Args:
            df: Normalized campaign DataFrame.
            channel: Channel name for context.

        Returns:
            ValidationResult with errors, warnings, and stats.
        """
        result = ValidationResult()

        self._check_minimum_rows(df, channel, result)
        self._check_required_columns(df, result)
        self._check_missing_values(df, result)
        self._check_date_range(df, result)
        self._check_date_gaps(df, result)
        self._check_negatives(df, result)
        self._check_zero_revenue_spend(df, result)
        self._check_campaign_consistency(df, result)
        self._compute_stats(df, channel, result)

        return result

    def validate_multi_channel(self, df: pd.DataFrame) -> ValidationResult:
        """Validate combined multi-channel dataset."""
        result = ValidationResult()

        self._check_minimum_rows(df, "combined", result)
        self._check_required_columns(df, result)
        self._check_missing_values(df, result)
        self._check_date_range(df, result)
        self._check_channel_alignment(df, result)
        self._compute_stats(df, "combined", result)

        return result

    # ── Individual Checks ────────────────────────────────────────────────────

    def _check_minimum_rows(
        self, df: pd.DataFrame, channel: str, result: ValidationResult
    ) -> None:
        if len(df) < self.MIN_ROWS:
            result.add_error(
                f"Channel '{channel}' has only {len(df)} rows. "
                f"Minimum {self.MIN_ROWS} rows required for reliable forecasting."
            )
        else:
            result.add_info(f"Row count OK: {len(df)} records.")

    def _check_required_columns(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        required = {"date", "channel", "spend", "revenue"}
        missing = required - set(df.columns)
        if missing:
            result.add_error(f"Missing required columns: {missing}")
        else:
            result.add_info("All required columns present.")

    def _check_missing_values(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        numeric_cols = ["impressions", "clicks", "spend", "conversions", "revenue"]
        for col in numeric_cols:
            if col not in df.columns:
                continue
            missing_count = df[col].isna().sum()
            missing_pct = missing_count / len(df) * 100
            if missing_pct > 20:
                result.add_error(
                    f"Column '{col}' has {missing_pct:.1f}% missing values — exceeds 20% threshold."
                )
            elif missing_pct > 5:
                result.add_warning(
                    f"Column '{col}' has {missing_pct:.1f}% missing values. Will be imputed."
                )

    def _check_date_range(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        if "date" not in df.columns:
            return

        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if dates.empty:
            result.add_error("No valid dates found in 'date' column.")
            return

        date_min = dates.min()
        date_max = dates.max()
        span_days = (date_max - date_min).days

        result.add_info(f"Date range: {date_min.date()} to {date_max.date()} ({span_days} days)")

        if span_days < 30:
            result.add_warning(
                f"Date range is only {span_days} days. "
                "At least 30 days recommended for robust forecasting."
            )

        # Check for future dates
        today = pd.Timestamp.now().normalize()
        future_rows = (dates > today).sum()
        if future_rows > 0:
            result.add_warning(f"{future_rows} rows have future dates. These will be excluded from training.")

    def _check_date_gaps(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        if "date" not in df.columns:
            return

        dates = pd.to_datetime(df["date"], errors="coerce").dropna().sort_values().unique()
        if len(dates) < 2:
            return

        gaps = []
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i - 1]).days
            if gap > self.MAX_GAP_DAYS:
                gaps.append((dates[i - 1], dates[i], gap))

        if gaps:
            for start, end, days in gaps[:5]:  # Show up to 5 gaps
                result.add_warning(
                    f"Data gap of {days} days between {start.date()} and {end.date()}."
                )

    def _check_negatives(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        for col in ["spend", "revenue", "impressions", "clicks"]:
            if col in df.columns:
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    result.add_warning(
                        f"Column '{col}' has {neg_count} negative values. "
                        "These may indicate refunds/adjustments."
                    )

    def _check_zero_revenue_spend(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        if "spend" in df.columns and "revenue" in df.columns:
            both_zero = ((df["spend"] == 0) & (df["revenue"] == 0)).sum()
            pct = both_zero / len(df) * 100
            if pct > 30:
                result.add_warning(
                    f"{pct:.1f}% of rows have both zero spend and revenue. "
                    "This may indicate missing data."
                )

    def _check_campaign_consistency(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        if "campaign" not in df.columns:
            return

        campaigns = df["campaign"].dropna().unique()
        result.add_info(f"Found {len(campaigns)} unique campaigns.")

        # Check for suspiciously similar campaign names (likely data quality issue)
        if len(campaigns) > 100:
            result.add_warning(
                f"High campaign diversity ({len(campaigns)} campaigns). "
                "Consider aggregating for cleaner forecasting."
            )

    def _check_channel_alignment(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        if "channel" not in df.columns:
            return

        channels = df["channel"].unique()
        result.add_info(f"Channels present: {list(channels)}")

        # Check date range alignment across channels
        channel_ranges = {}
        for ch in channels:
            ch_dates = pd.to_datetime(df[df["channel"] == ch]["date"], errors="coerce").dropna()
            if not ch_dates.empty:
                channel_ranges[ch] = (ch_dates.min(), ch_dates.max())

        if len(channel_ranges) > 1:
            starts = [v[0] for v in channel_ranges.values()]
            ends = [v[1] for v in channel_ranges.values()]
            start_spread = (max(starts) - min(starts)).days
            end_spread = (max(ends) - min(ends)).days

            if start_spread > 30:
                result.add_warning(
                    f"Channel start dates differ by {start_spread} days. "
                    "This may cause imbalanced channel comparisons."
                )

    def _compute_stats(
        self, df: pd.DataFrame, channel: str, result: ValidationResult
    ) -> None:
        stats: Dict[str, Any] = {"channel": channel, "rows": len(df)}

        if "spend" in df.columns:
            stats["total_spend"] = float(df["spend"].sum())
        if "revenue" in df.columns:
            stats["total_revenue"] = float(df["revenue"].sum())
        if "spend" in df.columns and "revenue" in df.columns:
            total_spend = df["spend"].sum()
            stats["blended_roas"] = float(
                df["revenue"].sum() / total_spend if total_spend > 0 else 0
            )
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"], errors="coerce").dropna()
            if not dates.empty:
                stats["date_from"] = str(dates.min().date())
                stats["date_to"] = str(dates.max().date())
                stats["date_span_days"] = int((dates.max() - dates.min()).days)

        if "channel" in df.columns:
            stats["channels"] = list(df["channel"].unique())

        result.stats = stats
