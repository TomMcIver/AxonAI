"""Tests for the 2PL IRT fitter.

Strategy: generate responses from known (theta_i, a_j, b_j) under the 2PL
model, fit, and check recovery within tolerance. Also covers the public
schema, heldout diagnostics, and file writers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.simulator.calibration.fit_2pl import (
    A_MAX,
    A_MIN,
    B_MAX,
    B_MIN,
    Fit2PLResult,
    _auc,
    _calibration_error,
    _logistic,
    fit_2pl,
    write_fit_report,
    write_item_params,
)


def _simulate(
    n_students: int,
    n_items: int,
    seed: int = 0,
    reps: int = 6,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Draw thetas, a, b; emit Bernoulli responses. Returns (df, theta, a, b)."""
    rng = np.random.default_rng(seed)
    theta = rng.normal(0.0, 1.0, size=n_students)
    theta -= theta.mean()  # centred, matches fit identifiability
    a = rng.uniform(0.8, 1.8, size=n_items)
    b = rng.uniform(-1.5, 1.5, size=n_items)

    rows = []
    for i in range(n_students):
        for j in range(n_items):
            for _ in range(reps):
                z = a[j] * (theta[i] - b[j])
                p = 1.0 / (1.0 + np.exp(-z))
                rows.append(
                    {
                        "user_id": i,
                        "problem_id": j,
                        "correct": bool(rng.random() < p),
                    }
                )
    return pd.DataFrame(rows), theta, a, b


@pytest.fixture(scope="module")
def simulated() -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    return _simulate(n_students=40, n_items=10, seed=0, reps=8)


class TestLogistic:
    def test_matches_closed_form(self) -> None:
        z = np.array([-20.0, -1.0, 0.0, 1.0, 20.0])
        p = _logistic(z)
        assert p[0] == pytest.approx(0.0, abs=1e-8)
        assert p[2] == pytest.approx(0.5)
        assert p[4] == pytest.approx(1.0, abs=1e-8)
        # Symmetry around 0.
        assert p[1] + p[3] == pytest.approx(1.0, abs=1e-10)

    def test_no_overflow_on_large_negative(self) -> None:
        z = np.array([-1000.0, 1000.0])
        p = _logistic(z)
        assert np.all(np.isfinite(p))


class TestAuc:
    def test_perfect_ranking(self) -> None:
        y = np.array([0, 0, 1, 1])
        score = np.array([0.1, 0.2, 0.8, 0.9])
        assert _auc(y, score) == pytest.approx(1.0)

    def test_reversed_ranking(self) -> None:
        y = np.array([0, 0, 1, 1])
        score = np.array([0.9, 0.8, 0.2, 0.1])
        assert _auc(y, score) == pytest.approx(0.0)

    def test_single_class_fallback(self) -> None:
        y = np.array([1, 1, 1])
        score = np.array([0.1, 0.5, 0.9])
        assert _auc(y, score) == 0.5


class TestCalibrationError:
    def test_zero_when_perfectly_calibrated(self) -> None:
        # With prob = empirical rate in each bin, calibration err = 0.
        y = np.array([0, 0, 1, 1])
        p = np.array([0.0, 0.0, 1.0, 1.0])
        assert _calibration_error(y, p, n_bins=5) == pytest.approx(0.0)


class TestFit2PL:
    def test_result_schema(self, simulated) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        assert isinstance(res, Fit2PLResult)
        assert set(res.item_params.columns) == {
            "item_id",
            "a",
            "b",
            "n_responses_train",
            "n_responses_heldout",
            "heldout_auc",
            "heldout_calibration_err",
        }
        assert set(res.theta_estimates.columns) == {"user_id", "theta"}

    def test_bounds_respected(self, simulated) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        assert (res.item_params["a"] >= A_MIN - 1e-9).all()
        assert (res.item_params["a"] <= A_MAX + 1e-9).all()
        assert (res.item_params["b"] >= B_MIN - 1e-9).all()
        assert (res.item_params["b"] <= B_MAX + 1e-9).all()

    def test_theta_identifiability(self, simulated) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        # Centring constraint: mean(theta) ~ 0.
        assert abs(res.theta_estimates["theta"].mean()) < 1e-6

    def test_parameter_recovery(self, simulated) -> None:
        df, true_theta, true_a, true_b = simulated
        res = fit_2pl(df, seed=1)

        # Correlations, not absolute values — JML has a scale indeterminacy
        # that bounds absorb, but ranks should match.
        b_hat = res.item_params.sort_values("item_id")["b"].to_numpy()
        a_hat = res.item_params.sort_values("item_id")["a"].to_numpy()
        theta_hat = res.theta_estimates.sort_values("user_id")["theta"].to_numpy()

        corr_b = np.corrcoef(b_hat, true_b)[0, 1]
        corr_theta = np.corrcoef(theta_hat, true_theta)[0, 1]
        corr_a = np.corrcoef(a_hat, true_a)[0, 1]
        assert corr_b > 0.9
        assert corr_theta > 0.85
        # `a` is the hardest to recover at small scale.
        assert corr_a > 0.3

    def test_heldout_auc_generally_above_half(self, simulated) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        auc = res.item_params["heldout_auc"].dropna()
        assert len(auc) > 0
        assert auc.mean() > 0.6

    def test_missing_columns_raise(self) -> None:
        bad = pd.DataFrame({"user_id": [0], "problem_id": [0]})
        with pytest.raises(KeyError):
            fit_2pl(bad)


class TestWriters:
    def test_item_params_roundtrip(self, simulated, tmp_path: Path) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        out = write_item_params(res, tmp_path / "items.parquet")
        assert out.exists()
        roundtrip = pd.read_parquet(out)
        assert list(roundtrip.columns) == list(res.item_params.columns)
        assert len(roundtrip) == len(res.item_params)

    def test_fit_report_written(self, simulated, tmp_path: Path) -> None:
        df, _, _, _ = simulated
        res = fit_2pl(df, seed=1)
        out = write_fit_report(res, tmp_path / "report.md")
        body = out.read_text()
        assert "# 2PL IRT fit report" in body
        assert "Items fit:" in body
