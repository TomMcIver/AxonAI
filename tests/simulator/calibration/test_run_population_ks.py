"""Unit tests for the population KS runner."""

from __future__ import annotations

import numpy as np
import pytest

from ml.simulator.calibration.run_population_ks import (
    _THETA_LOWER,
    _THETA_UPPER,
    _draw_latent_abilities,
    _qq_plot,
    _summary_stats,
)


def test_draw_latent_abilities_respects_bounds():
    priors = {"theta_mean": 0.0, "theta_std": 10.0}  # very wide to force clipping
    rng = np.random.default_rng(0)
    theta = _draw_latent_abilities(priors, n_students=5000, rng=rng)
    assert theta.min() >= _THETA_LOWER
    assert theta.max() <= _THETA_UPPER


def test_draw_latent_abilities_matches_moments():
    priors = {"theta_mean": 0.2, "theta_std": 0.8}
    rng = np.random.default_rng(42)
    theta = _draw_latent_abilities(priors, n_students=20_000, rng=rng)
    # Large n → sample mean / std within ~0.02 of the prior parameters.
    assert abs(theta.mean() - 0.2) < 0.02
    assert abs(theta.std(ddof=1) - 0.8) < 0.02


def test_draw_latent_abilities_is_seed_deterministic():
    priors = {"theta_mean": 0.0, "theta_std": 1.0}
    a = _draw_latent_abilities(priors, n_students=1000, rng=np.random.default_rng(1))
    b = _draw_latent_abilities(priors, n_students=1000, rng=np.random.default_rng(1))
    assert np.array_equal(a, b)


def test_summary_stats_shape():
    vals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    s = _summary_stats(vals)
    assert s["n"] == 5
    assert s["mean"] == pytest.approx(3.0)
    assert s["min"] == 1.0
    assert s["max"] == 5.0
    assert s["p50"] == pytest.approx(3.0)


def test_qq_plot_writes_file(tmp_path):
    sim = np.random.default_rng(0).normal(0, 1, size=1000)
    real = np.random.default_rng(1).normal(0, 1, size=1000)
    out = tmp_path / "qq.png"
    _qq_plot(sim, real, out)
    assert out.exists()
    assert out.stat().st_size > 0
