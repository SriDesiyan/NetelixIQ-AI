"""
NetElixIQ AI — Channel-Specific CSV Parsers
Normalizes Google Ads, Meta Ads, Microsoft Ads, Shopify, and GA4 exports
into a unified campaign record schema.
"""
import io
import logging
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Unified Schema ────────────────────────────────────────────────────────────
# Every parser must produce rows matching this schema:
UNIFIED_COLUMNS = [
    "date",          # YYYY-MM-DD
    "channel",       # google | meta | microsoft | shopify | ga4
    "campaign",      # Campaign name (optional)
    "impressions",   # float
    "clicks",        # float
    "spend",         # float (USD)
    "conversions",   # float
    "revenue",       # float (USD)
]

# ── Column alias maps (case-insensitive, space-stripped) ─────────────────────
GOOGLE_ADS_ALIASES = {
    "date": ["date", "day", "report date"],
    "campaign": ["campaign", "campaign name"],
    "impressions": ["impressions", "impr."],
    "clicks": ["clicks"],
    "spend": ["cost", "spend", "amount spent", "cost (usd)"],
    "conversions": ["conversions", "all conv.", "all conversions"],
    "revenue": ["conversion value", "conv. value", "all conv. value", "revenue"],
}

META_ADS_ALIASES = {
    "date": ["date", "day", "reporting starts", "report start", "date start", "reporting start"],
    "campaign": ["campaign name", "campaign", "ad set name", "adset name", "ad set", "adset"],
    "impressions": ["impressions"],
    "clicks": ["clicks (all)", "link clicks", "clicks"],
    "spend": ["amount spent (usd)", "amount spent", "spend"],
    "conversions": ["purchases", "conversions", "results"],
    "revenue": ["purchase conversion value", "website purchase roas", "revenue"],
}

MICROSOFT_ADS_ALIASES = {
    "date": ["date", "gregorian date", "time period"],
    "campaign": ["campaign name", "campaign"],
    "impressions": ["impressions"],
    "clicks": ["clicks"],
    "spend": ["spend", "revenue (usd)", "cost"],
    "conversions": ["conversions", "all conversions"],
    "revenue": ["revenue", "all conversion revenue"],
}

SHOPIFY_ALIASES = {
    "date": ["date", "order date", "created at", "day"],
    "campaign": ["source", "utm source", "marketing channel"],
    "impressions": ["sessions", "visits", "impressions"],
    "clicks": ["clicks", "sessions"],
    "spend": ["ad spend", "spend", "marketing spend"],
    "conversions": ["orders", "total orders", "conversions"],
    "revenue": ["total sales", "net sales", "revenue", "gross revenue"],
}

GA4_ALIASES = {
    "date": ["date", "day"],
    "campaign": ["campaign", "session campaign", "session default channel group"],
    "impressions": ["impressions", "screen page views"],
    "clicks": ["clicks", "sessions"],
    "spend": ["ad cost", "spend"],
    "conversions": ["conversions", "key events", "goal completions"],
    "revenue": ["revenue", "total revenue", "purchase revenue"],
}

CHANNEL_ALIASES = {
    "google": GOOGLE_ADS_ALIASES,
    "meta": META_ADS_ALIASES,
    "microsoft": MICROSOFT_ADS_ALIASES,
    "shopify": SHOPIFY_ALIASES,
    "ga4": GA4_ALIASES,
}


def _normalize_column_name(col: str) -> str:
    """Lowercase, strip spaces."""
    return col.strip().lower()


def _find_column(df_cols: List[str], aliases: List[str]) -> Optional[str]:
    """Find first matching column from aliases list."""
    normalized = {_normalize_column_name(c): c for c in df_cols}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    return None


def _map_columns(df: pd.DataFrame, alias_map: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Rename DataFrame columns using alias map.
    Fills missing mapped columns with 0.0 or empty string.
    """
    rename = {}
    for target_col, aliases in alias_map.items():
        found = _find_column(list(df.columns), aliases)
        if found:
            rename[found] = target_col

    df = df.rename(columns=rename)

    # Ensure all unified columns exist
    for col in UNIFIED_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0 if col not in ("date", "channel", "campaign") else ""

    return df[UNIFIED_COLUMNS]


def _parse_numeric(series: pd.Series) -> pd.Series:
    """Parse numeric columns, removing currency symbols and commas."""
    return (
        series.astype(str)
        .str.replace(r"[$,€£%]", "", regex=True)
        .str.strip()
        .replace({"": "0", "--": "0", "nan": "0"})
        .astype(float)
    )


def _parse_date(series: pd.Series) -> pd.Series:
    """Parse various date formats to YYYY-MM-DD string."""
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


def parse_channel_csv(
    content: bytes,
    channel: str,
    filename: str = "",
) -> pd.DataFrame:
    """
    Parse a CSV file for any supported channel.

    Args:
        content: Raw CSV bytes.
        channel: One of 'google', 'meta', 'microsoft', 'shopify', 'ga4'.
        filename: Original filename (for logging/error context).

    Returns:
        Normalized DataFrame with UNIFIED_COLUMNS + derived metrics.

    Raises:
        ValueError: If channel is unsupported or CSV cannot be parsed.
    """
    channel = channel.lower().strip()
    if channel not in CHANNEL_ALIASES:
        alias_map = {col: [col] for col in UNIFIED_COLUMNS}
    else:
        alias_map = CHANNEL_ALIASES[channel]

    try:
        # Try UTF-8 first, then latin-1 fallback
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8", thousands=",")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1", thousands=",")
    except Exception as e:
        raise ValueError(f"Cannot read CSV '{filename}': {e}")

    if df.empty:
        raise ValueError(f"CSV '{filename}' is empty.")

    logger.info(f"Parsing {channel} CSV '{filename}': {len(df)} rows, {len(df.columns)} cols")

    # Map columns to unified schema
    df = _map_columns(df, alias_map)

    # Parse dates
    df["date"] = _parse_date(df["date"])
    df = df.dropna(subset=["date"])

    # Parse numeric columns
    numeric_cols = ["impressions", "clicks", "spend", "conversions", "revenue"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _parse_numeric(df[col])

    # Set channel
    df["channel"] = channel

    # Derive computed metrics
    df["roas"] = np.where(df["spend"] > 0, df["revenue"] / df["spend"], 0.0)
    df["ctr"] = np.where(df["impressions"] > 0, df["clicks"] / df["impressions"] * 100, 0.0)
    df["cvr"] = np.where(df["clicks"] > 0, df["conversions"] / df["clicks"] * 100, 0.0)
    df["cpc"] = np.where(df["clicks"] > 0, df["spend"] / df["clicks"], 0.0)

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    logger.info(
        f"  Parsed {len(df)} records | spend={df['spend'].sum():.2f} | "
        f"revenue={df['revenue'].sum():.2f} | ROAS={df['roas'].mean():.2f}"
    )

    return df


def parse_multiple_channels(
    files: List[Dict[str, Any]],  # [{content: bytes, channel: str, filename: str}]
) -> pd.DataFrame:
    """
    Parse multiple channel CSV files and combine into one DataFrame.

    Args:
        files: List of dicts with keys: content, channel, filename.

    Returns:
        Combined normalized DataFrame sorted by date.
    """
    dfs = []
    errors = []

    for f in files:
        try:
            df = parse_channel_csv(
                content=f["content"],
                channel=f["channel"],
                filename=f.get("filename", ""),
            )
            dfs.append(df)
        except ValueError as e:
            errors.append(str(e))
            logger.error(f"Parse error: {e}")

    if errors and not dfs:
        raise ValueError(f"All files failed to parse: {'; '.join(errors)}")

    if not dfs:
        return pd.DataFrame(columns=UNIFIED_COLUMNS + ["roas", "ctr", "cvr", "cpc", "channel"])

    combined = pd.concat(dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
    logger.info(f"Combined dataset: {len(combined)} rows across {combined['channel'].nunique()} channels")
    return combined
