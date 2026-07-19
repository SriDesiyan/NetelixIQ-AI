"""
NetElixIQ AI — Test: Data Ingestion
Tests CSV parsing, normalization, and validation for all 5 channels.
"""
import os
import sys
import io
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.ingestion.parsers import parse_channel_csv, parse_multiple_channels
from backend.services.ingestion.validator import DataValidator


# ── Fixtures ──────────────────────────────────────────────────────────────────

GOOGLE_ADS_CSV = b"""Date,Campaign,Impressions,Clicks,Cost,Conversions,Conv. value
2026-01-01,Brand Campaign,10000,250,1200.50,12,3600.00
2026-01-02,Brand Campaign,11000,280,1350.00,14,4200.00
2026-01-03,Shopping,15000,400,2000.00,20,6000.00
2026-01-04,Shopping,14000,380,1900.00,18,5400.00
2026-01-05,Brand Campaign,10500,260,1250.00,13,3900.00
2026-01-06,Shopping,16000,420,2100.00,22,6600.00
2026-01-07,Brand Campaign,9500,230,1100.00,11,3300.00
"""

META_ADS_CSV = b"""Date Start,Ad Set Name,Amount Spent (USD),Impressions,Clicks (All),Purchases,Purchase Conversion Value
2026-01-01,Prospecting - Lookalike,800.00,25000,500,8,2400.00
2026-01-02,Retargeting - 30d,400.00,12000,300,6,1800.00
2026-01-03,Prospecting - Lookalike,850.00,27000,530,9,2700.00
2026-01-04,Retargeting - 30d,420.00,12500,310,7,2100.00
2026-01-05,Prospecting - Lookalike,900.00,28000,550,10,3000.00
2026-01-06,Retargeting - 30d,380.00,11000,280,5,1500.00
2026-01-07,Prospecting - Lookalike,780.00,24000,480,7,2100.00
"""

MINIMAL_CSV = b"""date,channel,spend,revenue
2026-01-01,test,100,300
2026-01-02,test,120,360
2026-01-03,test,110,330
2026-01-04,test,130,390
2026-01-05,test,140,420
2026-01-06,test,125,375
2026-01-07,test,135,405
"""


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestChannelParsers:

    def test_parse_google_ads(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="google.csv")
        assert len(df) == 7
        assert "date" in df.columns
        assert "spend" in df.columns
        assert "revenue" in df.columns
        assert "channel" in df.columns
        assert all(df["channel"] == "google")
        assert df["spend"].sum() > 0
        assert df["revenue"].sum() > 0

    def test_parse_meta_ads(self):
        df = parse_channel_csv(content=META_ADS_CSV, channel="meta", filename="meta.csv")
        assert len(df) == 7
        assert "date" in df.columns
        assert all(df["channel"] == "meta")
        assert df["revenue"].sum() > 0

    def test_parse_minimal_csv(self):
        """CSV with already-normalized column names."""
        df = parse_channel_csv(content=MINIMAL_CSV, channel="test", filename="test.csv")
        assert len(df) == 7
        assert df["spend"].sum() > 0

    def test_parse_empty_content_raises(self):
        with pytest.raises(ValueError):
            parse_channel_csv(content=b"", channel="google", filename="empty.csv")

    def test_parse_multi_channel(self):
        specs = [
            {"content": GOOGLE_ADS_CSV, "channel": "google", "filename": "g.csv"},
            {"content": META_ADS_CSV, "channel": "meta", "filename": "m.csv"},
        ]
        df = parse_multiple_channels(specs)
        assert len(df) == 14
        assert set(df["channel"].unique()) == {"google", "meta"}

    def test_roas_computed(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="google.csv")
        # ROAS = revenue / spend
        non_zero = df[df["spend"] > 0]
        computed_roas = non_zero["revenue"] / non_zero["spend"]
        # Allow small floating-point tolerance
        assert all(abs(computed_roas - non_zero["roas"]) < 0.01)

    def test_date_format_normalized(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="google.csv")
        # All dates should be parseable as datetime
        dates = pd.to_datetime(df["date"], errors="coerce")
        assert dates.isna().sum() == 0


# ── Validator Tests ───────────────────────────────────────────────────────────

class TestDataValidator:

    def setup_method(self):
        self.validator = DataValidator()

    def test_valid_data_passes(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="g.csv")
        result = self.validator.validate(df, channel="google")
        assert result.is_valid
        assert len(result.errors) == 0

    def test_too_few_rows_fails(self):
        df = pd.DataFrame([{
            "date": "2026-01-01", "channel": "google",
            "spend": 100, "revenue": 300,
        }])
        result = self.validator.validate(df)
        assert not result.is_valid
        assert any("rows" in e.lower() for e in result.errors)

    def test_missing_required_column_fails(self):
        df = pd.DataFrame([
            {"date": "2026-01-01", "spend": 100}  # missing revenue and channel
        ])
        result = self.validator.validate(df)
        assert not result.is_valid
        assert any("Missing required columns" in e for e in result.errors)

    def test_stats_computed(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="g.csv")
        result = self.validator.validate(df, channel="google")
        assert "total_spend" in result.stats
        assert "total_revenue" in result.stats
        assert result.stats["total_spend"] > 0

    def test_validate_multi_channel(self):
        specs = [
            {"content": GOOGLE_ADS_CSV, "channel": "google", "filename": "g.csv"},
            {"content": META_ADS_CSV, "channel": "meta", "filename": "m.csv"},
        ]
        df = parse_multiple_channels(specs)
        result = self.validator.validate_multi_channel(df)
        assert result.is_valid

    def test_to_dict_structure(self):
        df = parse_channel_csv(content=GOOGLE_ADS_CSV, channel="google", filename="g.csv")
        result = self.validator.validate(df)
        d = result.to_dict()
        assert "is_valid" in d
        assert "errors" in d
        assert "warnings" in d
        assert "stats" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
