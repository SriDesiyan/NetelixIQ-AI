"""
NetElixIQ AI — Prophet Forecasting Model
Facebook Prophet for trend + seasonality decomposition in marketing time-series.
Provides point forecasts and uncertainty intervals.
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Wrapper around Facebook Prophet for marketing revenue/ROAS forecasting.
    Handles Prophet unavailability gracefully with a fallback trend model.
    """

    def __init__(self, target_col: str = "revenue"):
        self.target_col = target_col
        self.model = None
        self._prophet_available = self._check_prophet()

    def _check_prophet(self) -> bool:
        try:
            from prophet import Prophet  # noqa
            return True
        except ImportError:
            logger.warning("Prophet not installed. Using fallback trend model.")
            return False

    def fit(self, df: pd.DataFrame) -> "ProphetForecaster":
        """
        Fit Prophet on daily aggregated data.

        Args:
            df: DataFrame with 'date' and target column.
        """
        if not self._prophet_available:
            self._fit_fallback(df)
            return self

        from prophet import Prophet

        train_df = df[["date", self.target_col]].copy()
        train_df = train_df.rename(columns={"date": "ds", self.target_col: "y"})
        train_df["ds"] = pd.to_datetime(train_df["ds"])
        train_df = train_df.dropna()

        self.model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.15,  # Slightly flexible for marketing data
            seasonality_mode="multiplicative",
            interval_width=0.80,  # 80% prediction interval
        )
        # Add monthly seasonality
        self.model.add_seasonality(name="monthly", period=30.5, fourier_order=5)

        self.model.fit(train_df)
        logger.info(f"Prophet fitted on {len(train_df)} rows for target='{self.target_col}'")
        return self

    def _fit_fallback(self, df: pd.DataFrame) -> None:
        """Simple exponential trend fallback when Prophet is unavailable."""
        y = df[self.target_col].values
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, deg=1)
        self._fallback_coeffs = coeffs
        self._fallback_last_val = y[-1] if len(y) > 0 else 0
        self._fallback_std = np.std(y) * 0.15

    def predict(self, horizon: int) -> pd.DataFrame:
        """
        Generate forecast for the next `horizon` days.

        Returns:
            DataFrame with columns: date, yhat, yhat_lower, yhat_upper
        """
        if not self._prophet_available or self.model is None:
            return self._predict_fallback(horizon)

        future = self.model.make_future_dataframe(periods=horizon)
        forecast = self.model.predict(future)

        # Return only future rows
        result = forecast.tail(horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result = result.rename(columns={"ds": "date"})
        result["date"] = result["date"].dt.strftime("%Y-%m-%d")
        result["yhat"] = result["yhat"].clip(lower=0)
        result["yhat_lower"] = result["yhat_lower"].clip(lower=0)
        result["yhat_upper"] = result["yhat_upper"].clip(lower=0)
        return result.reset_index(drop=True)

    def _predict_fallback(self, horizon: int) -> pd.DataFrame:
        """Fallback linear trend forecast."""
        from datetime import date, timedelta

        base = self._fallback_last_val
        slope = self._fallback_coeffs[0] if hasattr(self, "_fallback_coeffs") else 0
        std = getattr(self, "_fallback_std", base * 0.1)

        rows = []
        today = pd.Timestamp.now().normalize()
        for i in range(horizon):
            dt = today + pd.Timedelta(days=i + 1)
            yhat = max(0, base + slope * i + np.random.normal(0, std * 0.1))
            rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "yhat": yhat,
                "yhat_lower": max(0, yhat - 1.28 * std),
                "yhat_upper": yhat + 1.28 * std,
            })
        return pd.DataFrame(rows)

    def get_components(self) -> Optional[Dict[str, Any]]:
        """Return trend and seasonality components (Prophet only)."""
        if not self._prophet_available or self.model is None:
            return None
        return {
            "trend": "multiplicative",
            "seasonality_weekly": True,
            "seasonality_yearly": True,
        }

    def to_dict(self) -> dict:
        """Serialize Prophet model state to a JSON/dict representation."""
        state = {
            "target_col": self.target_col,
            "prophet_available": self._prophet_available,
        }
        if self._prophet_available and self.model is not None:
            try:
                from prophet.serialize import model_to_json
                state["prophet_json"] = model_to_json(self.model)
            except Exception as e:
                logger.warning(f"Failed to serialize Prophet model to JSON: {e}")
        
        # Serialize fallback parameters
        if hasattr(self, "_fallback_coeffs") and self._fallback_coeffs is not None:
            state["fallback_coeffs"] = self._fallback_coeffs.tolist()
        else:
            state["fallback_coeffs"] = None
        state["fallback_last_val"] = float(getattr(self, "_fallback_last_val", 0.0))
        state["fallback_std"] = float(getattr(self, "_fallback_std", 0.0))
        return state

    def from_dict(self, state: dict) -> "ProphetForecaster":
        """Reconstitute Prophet model state from JSON/dict representation."""
        self.target_col = state.get("target_col", "revenue")
        self._prophet_available = state.get("prophet_available", False)
        
        if self._prophet_available and "prophet_json" in state:
            try:
                from prophet.serialize import model_from_json
                self.model = model_from_json(state["prophet_json"])
            except Exception as e:
                logger.warning(f"Failed to deserialize Prophet model from JSON: {e}")
                self.model = None
        else:
            self.model = None

        # Reconstitute fallback parameters
        fallback_coeffs = state.get("fallback_coeffs")
        if fallback_coeffs is not None:
            self._fallback_coeffs = np.array(fallback_coeffs)
        else:
            self._fallback_coeffs = None
        self._fallback_last_val = state.get("fallback_last_val", 0.0)
        self._fallback_std = state.get("fallback_std", 0.0)
        return self
