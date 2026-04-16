"""Ridge regression: predict overall engagement score."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .base import TrainResult


def train_engagement_regressor(
    X: np.ndarray, y: np.ndarray, feature_columns: list[str]
) -> TrainResult:
    reg = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0, random_state=42)),
        ]
    )
    reg.fit(X, y)
    pred = reg.predict(X)
    r2 = float(r2_score(y, pred))
    return TrainResult(
        model=reg,
        feature_columns=feature_columns,
        train_score=r2,
        metrics={"r2_train": r2},
    )
