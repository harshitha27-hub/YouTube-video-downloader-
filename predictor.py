"""
predictor.py - Machine Learning prediction module.
Uses Scikit-Learn linear regression to forecast download counts and storage.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

from modules.database import DatabaseManager
from modules.logger import logger


class DownloadPredictor:
    """Predicts future download counts and storage usage."""

    def __init__(self):
        self.db    = DatabaseManager()
        self.model = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Convert monthly download history to X (month index) and y (count)."""
        monthly = self.db.get_monthly_counts()

        if len(monthly) < 2:
            # Synthesize minimal data to avoid empty-model errors
            X = np.arange(1, 7).reshape(-1, 1)
            y = np.array([10, 15, 20, 28, 35, 45], dtype=float)
            return X, y

        df  = pd.DataFrame(monthly)
        n   = len(df)
        X   = np.arange(1, n + 1, dtype=float).reshape(-1, 1)
        y   = df["cnt"].values.astype(float)
        return X, y

    def _train(self, degree: int = 2):
        """Fit a polynomial regression model."""
        X, y       = self._build_training_data()
        self.model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
        self.model.fit(X, y)
        self._n_months = len(X)      # last known month index

    # ── Public API ────────────────────────────────────────────────────────────

    def predict_downloads(self) -> Dict[str, int]:
        """Predict downloads for next week and next month."""
        self._train()
        n = self._n_months

        # Next-week heuristic: 1/4 of next month's predicted value
        next_month_idx = np.array([[n + 1]], dtype=float)
        next_month_val = max(0, int(self.model.predict(next_month_idx)[0]))
        next_week_val  = max(0, int(next_month_val * 0.25))

        # 3-month forecast
        three_months = 0
        for i in range(1, 4):
            three_months += max(0, int(self.model.predict(np.array([[n + i]]))[0]))

        logger.debug(f"Predicted downloads – week:{next_week_val}, month:{next_month_val}, 3mo:{three_months}")
        return {
            "next_week":    next_week_val,
            "next_month":   next_month_val,
            "next_3months": three_months,
        }

    def predict_storage(self) -> Dict[str, float]:
        """Predict storage usage in GB for the next 1 and 3 months."""
        stats        = self.db.get_stats()
        total_dl     = max(stats["total"], 1)
        total_gb     = stats["storage_gb"]
        avg_size_gb  = total_gb / total_dl  # average GB per download

        dl_pred      = self.predict_downloads()

        next_month_gb  = round(total_gb + dl_pred["next_month"]  * avg_size_gb, 2)
        next_3month_gb = round(total_gb + dl_pred["next_3months"] * avg_size_gb, 2)

        return {
            "current_gb":    round(total_gb, 2),
            "next_month_gb": next_month_gb,
            "next_3month_gb": next_3month_gb,
        }

    def predict_trends(self) -> Dict:
        """Return a summary of all predictions and a trend direction."""
        dl      = self.predict_downloads()
        storage = self.predict_storage()

        # Simple trend: compare next month vs last month
        X, y     = self._build_training_data()
        last_val = int(y[-1]) if len(y) > 0 else 0
        trend_dir = "📈 Growing" if dl["next_month"] > last_val else "📉 Declining"

        return {
            "downloads": dl,
            "storage":   storage,
            "trend_dir": trend_dir,
            "last_month_actual": last_val,
        }

    def get_formatted_predictions(self) -> str:
        """Return a human-readable prediction report string."""
        pred = self.predict_trends()
        dl   = pred["downloads"]
        st   = pred["storage"]

        lines = [
            "┌─────────────────────────────────────────┐",
            "│         📊 PREDICTION REPORT             │",
            "├─────────────────────────────────────────┤",
            "│  Predicted Downloads:                    │",
            f"│    Next Week  : {dl['next_week']:>5} downloads            │",
            f"│    Next Month : {dl['next_month']:>5} downloads            │",
            f"│    3 Months   : {dl['next_3months']:>5} downloads            │",
            "├─────────────────────────────────────────┤",
            "│  Predicted Storage:                      │",
            f"│    Current    : {st['current_gb']:>6.1f} GB               │",
            f"│    Next Month : {st['next_month_gb']:>6.1f} GB               │",
            f"│    3 Months   : {st['next_3month_gb']:>6.1f} GB               │",
            "├─────────────────────────────────────────┤",
            f"│  Trend: {pred['trend_dir']:<33}│",
            "└─────────────────────────────────────────┘",
        ]
        return "\n".join(lines)
