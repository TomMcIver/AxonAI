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


class TestRecoveryTheta:
    def test_joins_on_user_id(self) -> None:
        truth = pd.DataFrame({"user_id": [1, 2, 3], "theta": [0.0, 1.0, -1.0]})
        fitted = pd.DataFrame({"user_id": [1, 2, 3], "theta": [0.1, 0.9, -0.8]})
        out = metrics.recovery_theta(truth, fitted)
        assert out["n_users"] == 3
        assert out["theta_pearson"] > 0.9


class TestRecoveryBKT:
    def test_per_param_mae_when_all_match(self) -> None:
        truth = pd.DataFrame({
            "skill_id": [1, 2],
            "p_init": [0.1, 0.2],
            "p_transit": [0.1, 0.2],
            "p_slip": [0.05, 0.1],
            "p_guess": [0.2, 0.25],
        })
        out = metrics.recovery_bkt(truth, truth.copy())
        for p in ("p_init", "p_transit", "p_slip", "p_guess"):
            assert out[f"{p}_mae"] < 1e-9


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
