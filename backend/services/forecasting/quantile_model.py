"""
NetElixIQ AI — Quantile Regression for P10/P50/P90 Forecasting
Uses sklearn's QuantileRegressor to produce calibrated probabilistic forecasts.
Provides P10, P50 (median), and P90 prediction intervals directly.
"""
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

QUANTILES = [0.1, 0.5, 0.9]  # P10, P50, P90


class QuantileForecaster:
    """
    Trains separate quantile regression models for P10, P50, and P90.
    Produces well-calibrated prediction intervals for revenue/ROAS forecasting.
    """

    def __init__(self, target_col: str = "revenue"):
        self.target_col = target_col
        self.models: Dict[float, Pipeline] = {}
        self.feature_cols: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "QuantileForecaster":
        """
        Fit quantile models for P10, P50, P90.

        Args:
            X: Feature matrix.
            y: Target series.
        """
        self.feature_cols = list(X.columns)

        for q in QUANTILES:
            pipeline = Pipeline([
                ("scaler", RobustScaler()),
                ("model", QuantileRegressor(
                    quantile=q,
                    alpha=0.01,  # Mild L1 regularization
                    solver="highs",
                )),
            ])
            pipeline.fit(X, y)
            self.models[q] = pipeline
            logger.debug(f"  Quantile {q:.1f} model fitted.")

        logger.info(f"QuantileForecaster fitted | quantiles={QUANTILES} | features={len(self.feature_cols)}")
        return self

    def predict(self, X_future: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Predict P10, P50, P90 for future feature rows.

        Args:
            X_future: Feature DataFrame for future dates.

        Returns:
            Dict with keys 'p10', 'p50', 'p90' containing numpy arrays.
        """
        if not self.models:
            raise RuntimeError("QuantileForecaster not fitted.")

        # Align columns
        missing = set(self.feature_cols) - set(X_future.columns)
        for col in missing:
            X_future[col] = 0.0
        X_aligned = X_future[self.feature_cols]

        result = {}
        for q in QUANTILES:
            key = f"p{int(q * 100)}"
            pred = self.models[q].predict(X_aligned)
            result[key] = np.maximum(pred, 0)

        # Enforce monotonicity: p10 <= p50 <= p90
        result["p10"] = np.minimum(result["p10"], result["p50"])
        result["p90"] = np.maximum(result["p90"], result["p50"])

        return result

    def coverage_check(self, y_true: pd.Series, X_test: pd.DataFrame) -> float:
        """
        Compute empirical coverage of the 80% PI (P10-P90).
        Should be close to 80% for well-calibrated intervals.
        """
        preds = self.predict(X_test)
        coverage = np.mean((y_true.values >= preds["p10"]) & (y_true.values <= preds["p90"]))
        logger.info(f"PI coverage (target 80%): {coverage:.1%}")
        return float(coverage)
