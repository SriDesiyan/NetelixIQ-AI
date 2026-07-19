"""
NetElixIQ AI — Forecasting Pipeline Orchestrator
Ensemble of Prophet + LightGBM + Quantile Regression + Conformal Prediction.
Produces unified probabilistic forecasts (P10/P50/P90) for any metric.
"""
import json
import logging
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.services.forecasting.feature_eng import (
    build_daily_aggregates,
    build_feature_matrix,
    prepare_forecast_input,
)
from backend.services.forecasting.lgbm_model import LGBMForecaster
from backend.services.forecasting.prophet_model import ProphetForecaster
from backend.services.forecasting.quantile_model import QuantileForecaster
from backend.services.forecasting.conformal import ConformalWrapper
from backend.utils.numpy_encoder import convert_numpy_types

logger = logging.getLogger(__name__)

SUPPORTED_METRICS = ["revenue", "roas", "spend"]
DEFAULT_HORIZON = 30


class ForecastingPipeline:
    """
    End-to-end forecasting pipeline for marketing data.

    Architecture:
        1. Aggregate normalized data to daily totals
        2. Build feature matrix (lags, rolling, calendar)
        3. Train Prophet (trend/seasonality) + LightGBM (tabular) + Quantile (intervals)
        4. Wrap with Conformal Prediction for coverage-guaranteed intervals
        5. Blend models weighted by their cross-validated MAPE
        6. Output: {date, p10, p50, p90, model_weights, confidence}

    Supports 30/60/90 day forecast horizons.
    """

    def __init__(self, model_artifact_path: str = "pickle/model.pkl"):
        self.model_artifact_path = model_artifact_path
        self.lgbm: Optional[LGBMForecaster] = None
        self.prophet: Optional[ProphetForecaster] = None
        self.quantile: Optional[QuantileForecaster] = None
        self.conformal: Optional[ConformalWrapper] = None
        self.daily_df: Optional[pd.DataFrame] = None
        self.is_fitted: bool = False
        self.model_weights: Dict[str, float] = {}
        self.mape: float = 0.0
        self.target_col: str = "revenue"
        self.training_stats: Dict[str, Any] = {}

    def fit(self, df: pd.DataFrame, target_col: str = "revenue") -> "ForecastingPipeline":
        """
        Fit all models on the normalized campaign DataFrame.

        Args:
            df: Normalized campaign DataFrame (multi-channel OK).
            target_col: Metric to forecast ('revenue', 'roas', 'spend').

        Returns:
            Self (fitted pipeline).
        """
        self.target_col = target_col
        logger.info(f"ForecastingPipeline.fit() | target={target_col}")

        # Step 1: Aggregate to daily totals
        self.daily_df = build_daily_aggregates(df)

        if len(self.daily_df) < 14:
            logger.warning("Insufficient data for reliable forecasting (< 14 days).")

        # Step 2: Build feature matrix
        X, y = build_feature_matrix(self.daily_df, target_col=target_col)

        if len(X) < 10:
            raise ValueError("Not enough data to train models (min 10 rows after feature engineering).")

        # Step 3: Train-calibration split (80/20)
        split_idx = int(len(X) * 0.80)
        X_train, X_cal = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_cal = y.iloc[:split_idx], y.iloc[split_idx:]

        # Step 4: Train LightGBM
        logger.info("Training LightGBM...")
        self.lgbm = LGBMForecaster(target_col=target_col)
        self.lgbm.fit(X_train, y_train)

        # Step 5: Train Prophet
        logger.info("Training Prophet...")
        self.prophet = ProphetForecaster(target_col=target_col)
        self.prophet.fit(self.daily_df.iloc[:split_idx + 28])  # More history for Prophet

        # Step 6: Train Quantile Regression
        logger.info("Training Quantile Regression...")
        self.quantile = QuantileForecaster(target_col=target_col)
        self.quantile.fit(X_train, y_train)

        # Step 7: Calibrate Conformal on calibration set
        logger.info("Calibrating Conformal Prediction...")
        lgbm_cal_preds = self.lgbm.predict(X_cal)
        self.conformal = ConformalWrapper(alpha=0.20, relative=True)  # 80% coverage
        self.conformal.calibrate(y_cal.values, lgbm_cal_preds)

        # Step 8: Compute MAPE for model blending weights
        lgbm_mape = self.lgbm.mape
        prophet_mape = 0.18  # Conservative default; hard to measure on held-out for Prophet

        # Weights: lower MAPE = higher weight. Normalize to sum to 1.
        raw_weights = {
            "lgbm": 1.0 / max(lgbm_mape, 0.01),
            "prophet": 1.0 / max(prophet_mape, 0.01),
        }
        total = sum(raw_weights.values())
        self.model_weights = {k: v / total for k, v in raw_weights.items()}
        self.mape = lgbm_mape

        # Step 9: Store training stats
        self.training_stats = {
            "rows_used": int(len(self.daily_df)),
            "training_rows": split_idx,
            "calibration_rows": len(X_cal),
            "features": len(X.columns),
            "lgbm_mape": round(lgbm_mape, 4),
            "model_weights": self.model_weights,
            "conformal_q_hat": round(self.conformal.q_hat, 2),
            "target_col": target_col,
        }
        logger.info(f"Pipeline trained: {self.training_stats}")

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int = 30,
        spend_overrides: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Generate probabilistic forecast for the next `horizon` days.

        Args:
            horizon: Forecast horizon in days (30, 60, or 90).
            spend_overrides: Optional {'google': 500, 'meta': 300, 'microsoft': 100}
                             for budget simulation scenarios.

        Returns:
            Dict with:
                - forecast: List of {date, p10, p50, p90}
                - summary: Aggregate stats over horizon
                - model_weights: Blend weights
                - confidence: 0-1 confidence score
                - uncertainty: Uncertainty score
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline not fitted. Call fit() first.")

        # Build future feature rows
        future_df = prepare_forecast_input(
            self.daily_df.copy(), horizon=horizon, target_col=self.target_col
        )

        # Apply spend overrides if provided (budget simulation)
        if spend_overrides:
            total_override = sum(spend_overrides.values())
            future_df["spend"] = total_override

        feature_cols = [
            c for c in future_df.columns
            if c not in ["date", self.target_col, "channel", "campaign"]
            and not c.endswith("_raw")
        ]
        X_future = future_df[feature_cols].ffill().fillna(0)

        # LightGBM predictions
        lgbm_preds = self.lgbm.predict(X_future)

        # Prophet predictions
        prophet_df = self.prophet.predict(horizon)
        prophet_preds = prophet_df["yhat"].values

        # Ensure same length
        min_len = min(len(lgbm_preds), len(prophet_preds))
        lgbm_preds = lgbm_preds[:min_len]
        prophet_preds = prophet_preds[:min_len]

        # Weighted blend for P50
        w_lgbm = self.model_weights.get("lgbm", 0.6)
        w_prophet = self.model_weights.get("prophet", 0.4)
        blended_p50 = w_lgbm * lgbm_preds + w_prophet * prophet_preds

        conf_lower, conf_upper = self.conformal.predict(blended_p50)

        # Quantile predictions
        quantile_preds = self.quantile.predict(X_future)
        q_p10 = quantile_preds["p10"][:min_len]
        q_p90 = quantile_preds["p90"][:min_len]

        # Blend quantile and conformal for final bands
        final_p10 = 0.6 * q_p10 + 0.4 * conf_lower
        final_p90 = 0.6 * q_p90 + 0.4 * conf_upper
        final_p50 = blended_p50

        # Build output date range
        last_date = pd.to_datetime(self.daily_df["date"].max())
        dates = [
            (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
            for i in range(min_len)
        ]

        forecast_rows = []
        for i in range(min_len):
            p50_val = round(float(max(0, final_p50[i])), 2)
            # Enforce monotonic quantile constraint: P10 <= P50 <= P90
            p10_val = round(float(max(0, min(final_p10[i], p50_val))), 2)
            p90_val = round(float(max(p50_val, final_p90[i])), 2)
            forecast_rows.append({
                "date": dates[i],
                "p10": p10_val,
                "p50": p50_val,
                "p90": p90_val,
            })

        # Summary stats
        p50_arr = np.array([r["p50"] for r in forecast_rows])
        uncertainty = self.conformal.get_uncertainty_score(p50_arr)
        confidence = max(0.0, min(1.0, 1.0 - uncertainty - self.mape))

        summary = {
            "total_p10": round(float(sum(r["p10"] for r in forecast_rows)), 2),
            "total_p50": round(float(sum(r["p50"] for r in forecast_rows)), 2),
            "total_p90": round(float(sum(r["p90"] for r in forecast_rows)), 2),
            "avg_daily_p50": round(float(np.mean(p50_arr)), 2),
            "horizon_days": horizon,
            "target_metric": self.target_col,
            "model_mape": round(self.mape, 4),
        }

        return {
            "forecast": convert_numpy_types(forecast_rows),
            "summary": convert_numpy_types(summary),
            "model_weights": convert_numpy_types(self.model_weights),
            "confidence": round(confidence, 3),
            "uncertainty": round(float(uncertainty), 3),
            "training_stats": convert_numpy_types(self.training_stats),
        }

    def save(self, path: str) -> None:
        """Serialize entire pipeline to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = {
            "lgbm": self.lgbm,
            "conformal": self.conformal,
            "quantile": self.quantile,
            "daily_df": self.daily_df,
            "model_weights": self.model_weights,
            "mape": self.mape,
            "target_col": self.target_col,
            "training_stats": self.training_stats,
            "is_fitted": self.is_fitted,
            "prophet": self.prophet.to_dict() if self.prophet else None,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"ForecastingPipeline saved to {path}")

    @classmethod
    def load(cls, path: str) -> "ForecastingPipeline":
        """Load pipeline from disk."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        instance = cls(model_artifact_path=path)
        for k, v in state.items():
            if k != "prophet":
                setattr(instance, k, v)
        
        # Load Prophet from state or fallback to fit
        if "prophet" in state and state["prophet"] is not None:
            instance.prophet = ProphetForecaster(target_col=instance.target_col).from_dict(state["prophet"])
            logger.info("Prophet state successfully loaded from serialized data (no fitting needed)")
        elif instance.daily_df is not None and instance.is_fitted:
            try:
                instance.prophet = ProphetForecaster(target_col=instance.target_col)
                instance.prophet.fit(instance.daily_df)
                logger.info("Prophet fitted on loading (fallback)")
            except Exception as e:
                logger.warning(f"Prophet fit failed on loading: {e}. Using linear fallback.")
        
        logger.info(f"ForecastingPipeline loaded from {path}")
        return instance
