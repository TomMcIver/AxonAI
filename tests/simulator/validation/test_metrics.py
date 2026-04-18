"""Tests for validation metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.simulator.validation import metrics


class TestRecovery2PL:
    def test_perfect_recovery_yields_high_correlation(self) -> None:
        truth = pd.DataFrame({
            "problem_id": [1, 2, 3, 4],
            "a": [1.0, 1.5, 0.8, 2.0],
            "b": [-1.0, 0.0, 1.0, 2.0],
        })
        fitted = pd.DataFrame({
            "item_id": [1, 2, 3, 4],
            "a": [1.0, 1.5, 0.8, 2.0],
            "b": [-1.0, 0.0, 1.0, 2.0],
        })
        out = metrics.recovery_2pl(truth, fitted)
        assert out["n_items"] == 4
        assert out["a_pearson"] > 0.99
        assert out["b_pearson"] > 0.99
        assert out["a_mae"] < 1e-9

    def test_pearson_is_nan_with_single_item(self) -> None:
        truth = pd.DataFrame({"problem_id": [1], "a": [1.0], "b": [0.0]})
        fitted = pd.DataFrame({"item_id": [1], "a": [1.0], "b": [0.0]})
        out = metrics.recovery_2pl(truth, fitted)
        assert out["n_items"] == 1
        assert np.isnan(out["a_pearson"])
        assert np.isnan(out["b_pearson"])
        assert out["a_mae"] == 0.0

    def test_pearson_is_nan_when_truth_is_constant(self) -> None:
        truth = pd.DataFrame({"problem_id": [1, 2, 3], "a": [1.0, 1.0, 1.0], "b": [0.0, 1.0, -1.0]})
        fitted = pd.DataFrame({"item_id": [1, 2, 3], "a": [1.0, 1.2, 0.9], "b": [0.1, 0.9, -0.8]})
        out = metrics.recovery_2pl(truth, fitted)
        assert np.isnan(out["a_pearson"])
        assert not np.isnan(out["b_pearson"])


class TestRecoveryTheta:
    def test_joins_on_user_id(self) -> None:
        truth = pd.DataFrame({"user_id": [1, 2, 3], "theta": [0.0, 1.0, -1.0]})
        fitted = pd.DataFrame({"user_id": [1, 2, 3], "theta": [0.1, 0.9, -0.8]})
        out = metrics.recovery_theta(truth, fitted)
        assert out["n_users"] == 3
        assert out["theta_pearson"] > 0.9

    def test_pearson_is_nan_with_single_user(self) -> None:
        truth = pd.DataFrame({"user_id": [1], "theta": [0.0]})
        fitted = pd.DataFrame({"user_id": [1], "theta": [0.5]})
        out = metrics.recovery_theta(truth, fitted)
        assert out["n_users"] == 1
        assert np.isnan(out["theta_pearson"])
        assert out["theta_mae"] == 0.5

    def test_pearson_is_nan_when_fit_is_constant(self) -> None:
        truth = pd.DataFrame({"user_id": [1, 2, 3], "theta": [-1.0, 0.0, 1.0]})
        fitted = pd.DataFrame({"user_id": [1, 2, 3], "theta": [0.5, 0.5, 0.5]})
        out = metrics.recovery_theta(truth, fitted)
        assert np.isnan(out["theta_pearson"])


class TestKSCorrectRate:
    def test_identical_samples_give_tiny_ks(self) -> None:
        rng = np.random.default_rng(0)
        x = rng.uniform(0, 1, size=500)
        out = metrics.ks_correct_rate(x, x.copy())
        assert out["ks_statistic"] < 1e-9
        assert out["ks_pvalue"] > 0.99

    def test_shifted_samples_reject(self) -> None:
        rng = np.random.default_rng(1)
        a = rng.uniform(0.2, 0.4, size=200)
        b = rng.uniform(0.7, 0.9, size=200)
        out = metrics.ks_correct_rate(a, b)
        assert out["ks_statistic"] > 0.8
        assert out["ks_pvalue"] < 0.01


class TestResponseTimeFit:
    def test_recovers_lognormal_params_on_large_sample(self) -> None:
        rng = np.random.default_rng(0)
        mu, sigma = np.log(8000.0), 0.3
        sample = np.exp(rng.normal(mu, sigma, size=5000))
        out = metrics.response_time_fit(sample)
        assert abs(out["mu"] - mu) < 0.02
        assert abs(out["sigma"] - sigma) < 0.02


class TestLearningCurveSlope:
    def test_positive_slope_on_improving_cohort(self) -> None:
        rng = np.random.default_rng(0)
        rows = []
        for c in (1, 2):
            for i in range(60):
                p = 0.2 + 0.01 * i
                rows.append({"concept_id": c, "is_correct": bool(rng.random() < p)})
        df = pd.DataFrame(rows)
        out = metrics.learning_curve_slope(df)
        assert out["slope"] > 0.005
