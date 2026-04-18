"""Hand-computed tests for HLR retention.

    P(recall) = 2 ** (-hours_since_last / half_life_hours)
"""

from __future__ import annotations

import pytest

from ml.simulator.psychometrics.hlr import predict_recall, update_half_life


class TestPredictRecall:
    def test_zero_elapsed_is_full_recall(self) -> None:
        assert predict_recall(half_life_hours=24.0, hours_since_last=0.0) == pytest.approx(1.0)

    def test_one_half_life_is_half(self) -> None:
        assert predict_recall(half_life_hours=24.0, hours_since_last=24.0) == pytest.approx(0.5)

    def test_two_half_lives_is_quarter(self) -> None:
        assert predict_recall(half_life_hours=24.0, hours_since_last=48.0) == pytest.approx(0.25)

    def test_fractional_half_lives(self) -> None:
        # t = hl/2 → 2^-0.5 = 1/sqrt(2) ≈ 0.7071067811865476
        assert predict_recall(24.0, 12.0) == pytest.approx(0.7071067811865476)

    def test_invalid_half_life_raises(self) -> None:
        with pytest.raises(ValueError):
            predict_recall(half_life_hours=0.0, hours_since_last=1.0)
        with pytest.raises(ValueError):
            predict_recall(half_life_hours=-1.0, hours_since_last=1.0)

    def test_invalid_elapsed_raises(self) -> None:
        with pytest.raises(ValueError):
            predict_recall(half_life_hours=24.0, hours_since_last=-1.0)


class TestUpdateHalfLife:
    def test_correct_default_doubles(self) -> None:
        assert update_half_life(current_hl=24.0, is_correct=True,
                                response_time_ms=1000, features={}) == pytest.approx(48.0)

    def test_wrong_default_halves(self) -> None:
        assert update_half_life(current_hl=24.0, is_correct=False,
                                response_time_ms=1000, features={}) == pytest.approx(12.0)

    def test_features_override_correct(self) -> None:
        assert update_half_life(24.0, True, 1000, {"growth_correct": 1.5}) == pytest.approx(36.0)

    def test_features_override_wrong(self) -> None:
        assert update_half_life(24.0, False, 1000, {"growth_wrong": 0.25}) == pytest.approx(6.0)

    def test_min_clamp_prevents_collapse(self) -> None:
        # Repeated wrong at small hl: clamped at 0.25 hours.
        hl = 0.1
        for _ in range(10):
            hl = update_half_life(hl, False, 1000, {})
        assert hl == pytest.approx(0.25)

    def test_response_time_ignored_in_v1(self) -> None:
        # V1 rule is independent of response time.
        a = update_half_life(24.0, True, 500, {})
        b = update_half_life(24.0, True, 5_000_000, {})
        assert a == pytest.approx(b)
