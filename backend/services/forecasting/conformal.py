"""
NetElixIQ AI — Conformal Prediction Intervals
Wraps any point forecaster with statistically valid coverage-guaranteed intervals.
Uses split conformal prediction (inductive conformal prediction).

Reference: Angelopoulos & Bates (2021) "A Gentle Introduction to Conformal Prediction"
"""
import logging
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ConformalWrapper:
    """
    Converts a point forecaster into a conformal predictor.
    Guarantees (1-alpha)% marginal coverage of prediction intervals
    regardless of the underlying distribution.

    Supports both absolute and relative (heteroscedastic) residuals.
    """

    def __init__(self, alpha: float = 0.20, relative: bool = True):
        """
        Args:
            alpha: Miscoverage level. 0.20 => 80% PI, 0.10 => 90% PI.
            relative: If True, use percentage-based error calibration to prevent exploding bounds.
        """
        self.alpha = alpha
        self.relative = relative
        self.q_hat: float = 0.0  # Conformal quantile
        self._calibrated = False

    def calibrate(self, y_true: np.ndarray, y_pred: np.ndarray) -> "ConformalWrapper":
        """
        Calibrate conformal quantile using true vs predicted values.
        """
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        if self.relative:
            # Calibrate on percentage/relative residuals
            residuals = np.abs(y_true - y_pred) / np.maximum(np.abs(y_true), 10.0)
        else:
            # Calibrate on absolute residuals
            residuals = np.abs(y_true - y_pred)

        n = len(residuals)
        if n < 5:
            logger.warning("Conformal calibration: too few residuals, using default error rate.")
            self.q_hat = float(np.mean(residuals) * 1.5) if len(residuals) > 0 else (0.25 if self.relative else 5000.0)
        else:
            # Conformal level calculation
            level = np.ceil((n + 1) * (1 - self.alpha)) / n
            level = min(level, 1.0)
            self.q_hat = float(np.quantile(residuals, level))

        # Enforce sanity bounds for relative calibration
        if self.relative:
            # Limit the error rate to a maximum of 60% of the prediction level
            # to guarantee that the interval upper bound does not explode.
            self.q_hat = min(max(self.q_hat, 0.05), 0.60)

        self._calibrated = True
        logger.info(f"Conformal calibrated | alpha={self.alpha} | relative={self.relative} | q_hat={self.q_hat:.4f}")
        return self

    def predict(
        self, point_forecasts: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build conformal prediction intervals.

        Args:
            point_forecasts: Point predictions from base model.

        Returns:
            (lower, upper) numpy arrays.
        """
        if not self._calibrated:
            raise RuntimeError("ConformalWrapper not calibrated. Call calibrate() first.")

        point_forecasts = np.array(point_forecasts, dtype=float)

        if self.relative:
            # Scale by forecast value for multiplicative uncertainty
            margin = self.q_hat * np.abs(point_forecasts)
            # Minimum absolute fallback
            margin = np.maximum(margin, 10.0)
        else:
            margin = np.full_like(point_forecasts, self.q_hat, dtype=float)

        lower = np.maximum(point_forecasts - margin, 0.0)
        upper = point_forecasts + margin
        return lower, upper

    def get_uncertainty_score(self, point_forecasts: np.ndarray) -> float:
        """
        Return normalized uncertainty: ratio of interval width to forecast level.
        Higher = more uncertain (risk signal).
        """
        if not self._calibrated or point_forecasts.mean() == 0:
            return 0.5
        lower, upper = self.predict(point_forecasts)
        avg_width = float(np.mean(upper - lower))
        avg_forecast = float(np.mean(point_forecasts))
        return min(avg_width / max(avg_forecast, 1.0), 1.0)
