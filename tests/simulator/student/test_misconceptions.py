"""Tests for the misconception susceptibility sampler (PR B1).

Covers: mean-rate θ monotonicity, Beta-param derivation, sparse-map
schema, determinism under seed, cohort-level activity-rate correlation
with θ, and the scalar-θ reducer.
"""

from __future__ import annotations

import numpy as np
import pytest

from ml.simulator.student.misconceptions import (
    SusceptibilityConfig,
    SusceptibilitySampler,
    _beta_params,
    _mean_rate,
    scalar_theta_from_profile_thetas,
)


@pytest.fixture
def catalogue() -> np.ndarray:
    # Non-contiguous IDs to exercise the "preserve Eedi ID" contract.
    return np.array([0, 1, 2, 7, 11, 12, 100, 101, 500, 2612], dtype=np.int64)


@pytest.fixture
def cfg() -> SusceptibilityConfig:
    return SusceptibilityConfig()


class TestMeanRate:
    def test_neutral_theta_returns_base(self, cfg):
        assert _mean_rate(0.0, cfg) == pytest.approx(cfg.base_rate)

    def test_low_theta_raises_rate(self, cfg):
        # θ=-1 → base + coef*(0 - -1) = base + coef.
        assert _mean_rate(-1.0, cfg) == pytest.approx(
            cfg.base_rate + cfg.theta_coef
        )

    def test_high_theta_lowers_rate(self, cfg):
        low = _mean_rate(0.0, cfg)
        high = _mean_rate(2.0, cfg)
        assert high < low

    def test_clipped_at_floor(self, cfg):
        # Massive θ drives raw mean well below floor.
        assert _mean_rate(100.0, cfg) == pytest.approx(cfg.min_mean_rate)

    def test_clipped_at_ceiling(self, cfg):
        # Very low θ drives raw mean above ceiling.
        assert _mean_rate(-100.0, cfg) == pytest.approx(cfg.max_mean_rate)


class TestBetaParams:
    def test_positive_interior_mean(self):
        a, b = _beta_params(0.2, 8.0)
        assert a == pytest.approx(1.6)
        assert b == pytest.approx(6.4)

    def test_guards_degenerate_zero_mean(self):
        a, b = _beta_params(0.0, 8.0)
        assert a > 0.0
        assert b > 0.0

    def test_guards_degenerate_one_mean(self):
        a, b = _beta_params(1.0, 8.0)
        assert a > 0.0
        assert b > 0.0


class TestSamplerSchema:
    def test_rejects_empty_catalogue(self):
        with pytest.raises(ValueError, match="empty"):
            SusceptibilitySampler(misconception_ids=np.array([], dtype=np.int64))

    def test_rejects_duplicates(self):
        with pytest.raises(ValueError, match="duplicates"):
            SusceptibilitySampler(misconception_ids=np.array([1, 1, 2]))

    def test_rejects_non_1d(self):
        with pytest.raises(ValueError, match="1-D"):
            SusceptibilitySampler(
                misconception_ids=np.array([[1, 2], [3, 4]])
            )

    def test_returns_dict_with_int_keys_and_float_values(self, catalogue):
        s = SusceptibilitySampler(misconception_ids=catalogue)
        out = s.draw(0.0, np.random.default_rng(0))
        assert isinstance(out, dict)
        for k, v in out.items():
            assert isinstance(k, int)
            assert isinstance(v, float)

    def test_keys_are_subset_of_catalogue(self, catalogue):
        s = SusceptibilitySampler(misconception_ids=catalogue)
        for seed in range(20):
            out = s.draw(0.0, np.random.default_rng(seed))
            assert set(out.keys()) <= set(int(x) for x in catalogue)

    def test_weights_within_configured_range(self, catalogue):
        s = SusceptibilitySampler(misconception_ids=catalogue)
        for seed in range(20):
            out = s.draw(0.0, np.random.default_rng(seed))
            for w in out.values():
                assert s.config.weight_min <= w <= s.config.weight_max


class TestSamplerDeterminism:
    def test_same_seed_same_output(self, catalogue):
        s = SusceptibilitySampler(misconception_ids=catalogue)
        a = s.draw(0.0, np.random.default_rng(123))
        b = s.draw(0.0, np.random.default_rng(123))
        assert a == b

    def test_different_seed_different_output(self, catalogue):
        s = SusceptibilitySampler(misconception_ids=catalogue)
        a = s.draw(0.0, np.random.default_rng(1))
        b = s.draw(0.0, np.random.default_rng(2))
        assert a != b


class TestSamplerPopulation:
    def test_activity_rate_negatively_correlates_with_theta(self, catalogue):
        """Lower-θ cohort should have larger |active| on average."""
        s = SusceptibilitySampler(misconception_ids=catalogue)
        lows, highs = [], []
        for seed in range(500):
            low_rng = np.random.default_rng(seed)
            high_rng = np.random.default_rng(seed + 10_000)
            lows.append(len(s.draw(-1.5, low_rng)))
            highs.append(len(s.draw(+1.5, high_rng)))
        assert np.mean(lows) > np.mean(highs)

    def test_mean_activity_rate_tracks_formula(self, catalogue, cfg):
        """E[|active| / N] ~ E[r] = configured mean_r(θ) under full Bernoulli."""
        s = SusceptibilitySampler(misconception_ids=catalogue)
        counts = []
        for seed in range(2_000):
            out = s.draw(0.0, np.random.default_rng(seed))
            counts.append(len(out) / len(catalogue))
        observed = float(np.mean(counts))
        expected = _mean_rate(0.0, cfg)
        assert abs(observed - expected) < 0.02


class TestScalarThetaReducer:
    def test_empty_returns_zero(self):
        assert scalar_theta_from_profile_thetas([]) == 0.0

    def test_mean_of_values(self):
        assert scalar_theta_from_profile_thetas([1.0, 2.0, 3.0]) == pytest.approx(2.0)

    def test_accepts_dict_values_view(self):
        d = {1: -0.5, 2: 0.5}
        assert scalar_theta_from_profile_thetas(d.values()) == pytest.approx(0.0)
