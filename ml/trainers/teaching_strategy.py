"""Logistic regression: predict strategy success (success_rate >= 0.5)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .base import TrainResult


def train_strategy_classifier(
    X: np.ndarray, y: np.ndarray, feature_columns: list[str]
) -> TrainResult:
    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    clf.fit(X, y)
    pred = clf.predict(X)
    acc = float(accuracy_score(y, pred))
    return TrainResult(
        model=clf,
        feature_columns=feature_columns,
        train_score=acc,
        metrics={"accuracy": acc},
    )
