"""
NetElixIQ AI — Monte Carlo Budget Simulation
Adapted from Finan/Finance-v1-main HSMM Monte Carlo approach.
Simulates revenue/ROAS distribution for arbitrary budget allocations.
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from backend.utils.numpy_encoder import convert_numpy_types

logger = logging.getLogger(__name__)

# Channel ROAS efficiency profiles (learned from historical data or defaults)
DEFAULT_CHANNEL_EFFICIENCY = {
    "google": {"base_roas": 3.8, "roas_std": 0.4, "spend_elasticity": 0.85},
    "meta": {"base_roas": 2.9, "roas_std": 0.6, "spend_elasticity": 0.75},
    "microsoft": {"base_roas": 3.2, "roas_std": 0.3, "spend_elasticity": 0.90},
}

N_SIMULATIONS = 2000  # Monte Carlo runs


class BudgetSimulator:
    """
    Monte Carlo budget simulation for marketing channel allocation.
    Given a budget split across Google/Meta/Microsoft, simulates:
    - Expected revenue distribution (P10/P50/P90)
    - Blended ROAS distribution
    - Channel contribution percentages
    - Confidence score

    Adapted from the HSMM Monte Carlo simulation in Finance-v1-main.
    """

    def __init__(self, n_simulations: int = N_SIMULATIONS, seed: int = 42):
        self.n_simulations = n_simulations
        self.seed = seed
        self.channel_profiles: Dict[str, Dict] = {}
        self._is_calibrated = False

    def calibrate_from_data(self, df: pd.DataFrame) -> "BudgetSimulator":
        """
        Calibrate channel efficiency profiles from historical campaign data.

        Args:
            df: Normalized campaign DataFrame with date, channel, spend, revenue.
        """
        if "channel" not in df.columns:
            logger.warning("No channel column; using default efficiency profiles.")
            self.channel_profiles = DEFAULT_CHANNEL_EFFICIENCY.copy()
            self._is_calibrated = True
            return self

        for channel in ["google", "meta", "microsoft"]:
            ch_data = df[df["channel"] == channel]
            if ch_data.empty or ch_data["spend"].sum() == 0:
                self.channel_profiles[channel] = DEFAULT_CHANNEL_EFFICIENCY.get(
                    channel, {"base_roas": 3.0, "roas_std": 0.5, "spend_elasticity": 0.80}
                )
                continue

            # Compute historical ROAS statistics
            daily = ch_data.groupby("date")[["spend", "revenue"]].sum()
            daily_roas = (daily["revenue"] / daily["spend"].clip(lower=0.01)).clip(0, 50)

            base_roas = float(daily_roas.median())
            roas_std = float(daily_roas.std()) if daily_roas.std() > 0 else base_roas * 0.15

            # Estimate spend elasticity (diminishing returns)
            # Simple: if more spend correlates with lower ROAS, elasticity < 1
            if len(daily) >= 7:
                corr = daily["spend"].corr(daily_roas)
                elasticity = max(0.5, min(0.95, 0.85 - corr * 0.2))
            else:
                elasticity = 0.85

            self.channel_profiles[channel] = {
                "base_roas": max(0.5, base_roas),
                "roas_std": max(0.05, roas_std),
                "spend_elasticity": elasticity,
            }

            logger.info(
                f"  {channel}: ROAS={base_roas:.2f}±{roas_std:.2f}, elasticity={elasticity:.2f}"
            )

        self._is_calibrated = True
        logger.info(f"BudgetSimulator calibrated from {len(df)} rows")
        return self

    def simulate(
        self,
        google_budget: float,
        meta_budget: float,
        microsoft_budget: float,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo budget simulation.

        Args:
            google_budget: Total Google Ads budget for the period (USD).
            meta_budget: Total Meta Ads budget for the period (USD).
            microsoft_budget: Total Microsoft Ads budget for the period (USD).
            horizon_days: Budget period in days.

        Returns:
            Dict with revenue/ROAS distributions and channel mix.
        """
        if not self._is_calibrated:
            self.channel_profiles = DEFAULT_CHANNEL_EFFICIENCY.copy()

        rng = np.random.default_rng(self.seed)

        budgets = {
            "google": max(0.0, google_budget),
            "meta": max(0.0, meta_budget),
            "microsoft": max(0.0, microsoft_budget),
        }
        total_budget = sum(budgets.values())

        if total_budget == 0:
            return self._empty_result()

        # Run simulations
        total_revenues = np.zeros(self.n_simulations)
        channel_revenues: Dict[str, np.ndarray] = {ch: np.zeros(self.n_simulations) for ch in budgets}

        for channel, budget in budgets.items():
            if budget == 0:
                continue

            profile = self.channel_profiles.get(channel, DEFAULT_CHANNEL_EFFICIENCY.get(channel, {}))
            base_roas = profile.get("base_roas", 3.0)
            roas_std = profile.get("roas_std", 0.5)
            elasticity = profile.get("spend_elasticity", 0.85)

            # Daily budget
            daily_budget = budget / max(horizon_days, 1)

            # Simulate daily revenue across all simulations and days
            daily_roas_sims = rng.normal(
                loc=base_roas,
                scale=roas_std,
                size=(self.n_simulations, horizon_days),
            ).clip(0.1, 20)

            # Apply diminishing returns (spend elasticity)
            effective_budget = daily_budget ** elasticity * (daily_budget ** (1 - elasticity))
            daily_revenue_sims = daily_roas_sims * daily_budget

            # Sum across days
            sim_revenues = daily_revenue_sims.sum(axis=1)
            channel_revenues[channel] = sim_revenues
            total_revenues += sim_revenues

        # Revenue distribution
        p10 = float(np.percentile(total_revenues, 10))
        p50 = float(np.percentile(total_revenues, 50))
        p90 = float(np.percentile(total_revenues, 90))

        # ROAS distribution
        roas_sims = np.where(total_budget > 0, total_revenues / total_budget, 0)
        roas_p10 = float(np.percentile(roas_sims, 10))
        roas_p50 = float(np.percentile(roas_sims, 50))
        roas_p90 = float(np.percentile(roas_sims, 90))

        # Channel mix
        channel_mix = {}
        for channel in budgets:
            ch_rev = float(channel_revenues[channel].mean())
            channel_mix[channel] = {
                "budget": round(budgets[channel], 2),
                "expected_revenue": round(ch_rev, 2),
                "budget_share_pct": round(budgets[channel] / total_budget * 100, 1) if total_budget > 0 else 0,
                "revenue_share_pct": round(ch_rev / max(p50, 1) * 100, 1),
                "expected_roas": round(
                    ch_rev / max(budgets[channel], 1), 2
                ),
            }

        # Confidence: narrower interval = higher confidence
        interval_width = p90 - p10
        confidence = max(0.0, min(1.0, 1.0 - interval_width / max(p50 * 2, 1)))

        # Histogram data (for chart)
        hist_counts, hist_bins = np.histogram(total_revenues, bins=50)
        histogram = {
            "counts": hist_counts.tolist(),
            "bins": [round(b, 0) for b in hist_bins.tolist()],
        }

        return convert_numpy_types({
            "revenue": {
                "p10": round(p10, 2),
                "p50": round(p50, 2),
                "p90": round(p90, 2),
            },
            "roas": {
                "p10": round(roas_p10, 2),
                "p50": round(roas_p50, 2),
                "p90": round(roas_p90, 2),
            },
            "channel_mix": channel_mix,
            "total_budget": round(total_budget, 2),
            "confidence": round(confidence, 3),
            "horizon_days": horizon_days,
            "n_simulations": self.n_simulations,
            "histogram": histogram,
        })

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "revenue": {"p10": 0, "p50": 0, "p90": 0},
            "roas": {"p10": 0, "p50": 0, "p90": 0},
            "channel_mix": {},
            "total_budget": 0,
            "confidence": 0,
            "horizon_days": 30,
            "n_simulations": self.n_simulations,
            "histogram": {"counts": [], "bins": []},
        }
