"""Hand-computed tests for 2PL IRT.

Closed-form expected values are derived from
    P = 1 / (1 + exp(-a*(theta - b)))
in each test's comment.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ml.simulator.psychometrics.irt_2pl import (
    log_likelihood,
    prob_correct,
    sample_response,
)


class TestProbCorrect:
    def test_at_difficulty_is_half(self) -> None:
        # theta == b  →  z = 0  →  P = 0.5
        assert prob_correct(theta=0.0, a=1.0, b=0.0) == pytest.approx(0.5)
        assert prob_correct(theta=1.5, a=2.3, b=1.5) == pytest.approx(0.5)

    def test_one_logit_above(self) -> None:
        # z = 1 → P = 1 / (1 + e^-1) = 0.7310585786300049
        expected = 1.0 / (1.0 + math.exp(-1.0))
        assert prob_correct(theta=1.0, a=1.0, b=0.0) == pytest.approx(expected)

    def test_one_logit_below(self) -> None:
        # z = -1 → P = 1 / (1 + e^1) = 0.2689414213699951
        expected = 1.0 / (1.0 + math.exp(1.0))
        assert prob_correct(theta=-1.0, a=1.0, b=0.0) == pytest.approx(expected)

    def test_discrimination_scales_slope(self) -> None:
        # a=2 makes the same theta-b gap twice as decisive.
        p_low_a = prob_correct(theta=0.5, a=1.0, b=0.0)
        p_high_a = prob_correct(theta=0.5, a=2.0, b=0.0)
        assert p_high_a > p_low_a
        # a=2, theta=0.5, b=0 → z = 1 → P = 0.7310585786300049
        assert p_high_a == pytest.approx(1.0 / (1.0 + math.exp(-1.0)))

    def test_numerical_stability_large_positive(self) -> None:
        assert prob_correct(theta=100.0, a=1.0, b=0.0) == pytest.approx(1.0)

    def test_numerical_stability_large_negative(self) -> None:
        assert prob_correct(theta=-100.0, a=1.0, b=0.0) == pytest.approx(0.0, abs=1e-30)

    def test_monotone_in_theta(self) -> None:
        ps = [prob_correct(theta=t, a=1.0, b=0.0) for t in [-3.0, -1.0, 0.0, 1.0, 3.0]]
        assert all(ps[i] < ps[i + 1] for i in range(len(ps) - 1))


class TestSampleResponse:
    def test_deterministic_given_seed(self) -> None:
        rng_a = np.random.default_rng(seed=123)
        rng_b = np.random.default_rng(seed=123)
        results_a = [sample_response(0.0, 1.0, 0.0, rng_a) for _ in range(100)]
        results_b = [sample_response(0.0, 1.0, 0.0, rng_b) for _ in range(100)]
        assert results_a == results_b

    def test_always_correct_when_p_near_one(self) -> None:
        rng = np.random.default_rng(seed=0)
        # theta well above b with high discrimination → P ~ 1
        assert all(sample_response(10.0, 2.0, 0.0, rng) for _ in range(50))

    def test_always_wrong_when_p_near_zero(self) -> None:
        rng = np.random.default_rng(seed=0)
        assert not any(sample_response(-10.0, 2.0, 0.0, rng) for _ in range(50))

    def test_empirical_rate_matches_probability(self) -> None:
        rng = np.random.default_rng(seed=7)
        # theta=0.5, a=1, b=0 → P ≈ 0.622
        p_true = prob_correct(0.5, 1.0, 0.0)
        n = 5000
        hits = sum(sample_response(0.5, 1.0, 0.0, rng) for _ in range(n))
        assert abs(hits / n - p_true) < 0.02


class TestLogLikelihood:
    def test_single_correct_at_threshold(self) -> None:
        # P = 0.5  →  log P = -log(2)
        ll = log_likelihood([True], [0.0], [(1.0, 0.0)])
        assert ll == pytest.approx(-math.log(2.0))

    def test_single_wrong_at_threshold(self) -> None:
        ll = log_likelihood([False], [0.0], [(1.0, 0.0)])
        assert ll == pytest.approx(-math.log(2.0))

    def test_sum_over_multiple_responses(self) -> None:
        # Two responses, each at P=0.5. LL = 2 * log(0.5).
        ll = log_likelihood([True, False], [0.0, 0.0], [(1.0, 0.0), (1.0, 0.0)])
        assert ll == pytest.approx(2.0 * -math.log(2.0))

    def test_mixed_probabilities(self) -> None:
        # Response 1: correct at P = 1/(1+e^-1) ≈ 0.7311 → log 0.7311
        # Response 2: wrong   at P_wrong = 1 - 1/(1+e^-1) → log 0.2689
        p_correct = 1.0 / (1.0 + math.exp(-1.0))
        p_wrong = 1.0 - p_correct
        expected = math.log(p_correct) + math.log(p_wrong)
        ll = log_likelihood([True, False], [1.0, 1.0], [(1.0, 0.0), (1.0, 0.0)])
        assert ll == pytest.approx(expected)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            log_likelihood([True, False], [0.0], [(1.0, 0.0)])

    def test_stable_on_extreme_logits(self) -> None:
        # z = 100: log P(correct) should be ~0, not NaN
        ll = log_likelihood([True], [100.0], [(1.0, 0.0)])
        assert math.isfinite(ll)
        assert ll == pytest.approx(0.0, abs=1e-30)
