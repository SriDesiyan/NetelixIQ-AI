"""
NetElixIQ AI — LightGBM Forecasting Model
Feature-rich gradient boosting for revenue prediction.
Uses lag features, rolling statistics, and spend predictors.
"""
import logging
import pickle
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)


class LGBMForecaster:
    """
    LightGBM-based marketing revenue forecaster.
    Trains on tabular features (lags, rolling stats, spend, calendar).
    Falls back to XGBoost if LightGBM is unavailable.
    """

    def __init__(self, target_col: str = "revenue", n_estimators: int = 500):
        self.target_col = target_col
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = RobustScaler()
        self.feature_cols: List[str] = []
        self.mape: float = 0.0
        self._lgbm_available = self._check_lgbm()

    def _check_lgbm(self) -> bool:
        try:
            import lightgbm  # noqa
            return True
        except ImportError:
            logger.warning("LightGBM not installed. Trying XGBoost fallback.")
            return False

    def _get_model(self):
        """Get LightGBM or XGBoost model."""
        if self._lgbm_available:
            import lightgbm as lgb
            return lgb.LGBMRegressor(
                n_estimators=self.n_estimators,
                learning_rate=0.05,
                num_leaves=31,
                max_depth=6,
                min_child_samples=10,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                reg_alpha=0.1,
                reg_lambda=0.1,
                random_state=42,
                verbose=-1,
            )
        else:
            try:
                from xgboost import XGBRegressor
                logger.info("Using XGBoost as LightGBM fallback.")
                return XGBRegressor(
                    n_estimators=self.n_estimators,
                    learning_rate=0.05,
                    max_depth=6,
                    random_state=42,
                    verbosity=0,
                )
            except ImportError:
                from sklearn.ensemble import GradientBoostingRegressor
                logger.warning("Using sklearn GradientBoostingRegressor as final fallback.")
                return GradientBoostingRegressor(
                    n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42
                )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LGBMForecaster":
        """
        Fit the model with time-series cross-validation.

        Args:
            X: Feature matrix.
            y: Target series.
        """
        self.feature_cols = list(X.columns)

        # Time-series CV for MAPE estimation
        tscv = TimeSeriesSplit(n_splits=3)
        mapes = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            model = self._get_model()

            if self._lgbm_available:
                import lightgbm as lgb
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=-1)],
                )
            else:
                model.fit(X_train, y_train)

            y_pred = model.predict(X_val)
            y_pred = np.maximum(y_pred, 0)

            if y_val.mean() > 0:
                mapes.append(mean_absolute_percentage_error(y_val, y_pred))

        self.mape = float(np.mean(mapes)) if mapes else 0.15

        # Train final model on all data
        self.model = self._get_model()
        if self._lgbm_available:
            import lightgbm as lgb
            self.model.fit(
                X, y,
                callbacks=[lgb.log_evaluation(period=-1)],
            )
        else:
            self.model.fit(X, y)

        logger.info(
            f"LGBMForecaster fitted | features={len(self.feature_cols)} | MAPE={self.mape:.3f}"
        )
        return self

    def predict(self, X_future: pd.DataFrame) -> np.ndarray:
        """
        Predict for future feature rows.

        Args:
            X_future: Feature DataFrame for future dates.

        Returns:
            Array of predictions.
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        # Align features
        missing = set(self.feature_cols) - set(X_future.columns)
        for col in missing:
            X_future[col] = 0.0

        X_aligned = X_future[self.feature_cols]
        preds = self.model.predict(X_aligned)
        return np.maximum(preds, 0)

    def feature_importance(self) -> Dict[str, float]:
        """Return feature importances as dict."""
        if self.model is None:
            return {}
        try:
            importances = self.model.feature_importances_
            return {
                col: float(imp)
                for col, imp in zip(self.feature_cols, importances)
            }
        except Exception:
            return {}

    def save(self, path: str) -> None:
        """Serialize model to disk."""
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "feature_cols": self.feature_cols,
                "mape": self.mape,
                "target_col": self.target_col,
            }, f)
        logger.info(f"LGBMForecaster saved to {path}")

    @classmethod
    def load(cls, path: str) -> "LGBMForecaster":
        """Load model from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        instance = cls(target_col=data["target_col"])
        instance.model = data["model"]
        instance.feature_cols = data["feature_cols"]
        instance.mape = data["mape"]
        logger.info(f"LGBMForecaster loaded from {path}")
        return instance
