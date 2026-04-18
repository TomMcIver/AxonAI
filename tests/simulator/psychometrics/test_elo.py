"""Hand-computed tests for Elo.

Closed-form expected values:
    E = 1 / (1 + 10 ** ((r_q - r_s) / 400))
    r_s' = r_s + K * (actual - E),  r_q' = r_q - K * (actual - E)
    k_factor linearly anneals 40 → 10 over 30 attempts, held at 10.
"""

from __future__ import annotations

import pytest

from ml.simulator.psychometrics.elo import expected, k_factor, update


class TestExpected:
    def test_equal_ratings_is_half(self) -> None:
        assert expected(1000.0, 1000.0) == pytest.approx(0.5)

    def test_student_200_above(self) -> None:
        # 10 ^ ((1000 - 1200) / 400) = 10 ^ -0.5 = 0.31622776601683794
        # E = 1 / (1 + 0.31622...) = 0.7597469266479578
        assert expected(1200.0, 1000.0) == pytest.approx(0.7597469266479578)

    def test_student_200_below(self) -> None:
        # 10 ^ 0.5 = 3.1622776601683795
        # E = 1 / (1 + 3.1622...) = 0.24025307335204222
        assert expected(800.0, 1000.0) == pytest.approx(0.24025307335204222)

    def test_sum_to_one_symmetry(self) -> None:
        # Elo is symmetric: E(A, B) + E(B, A) = 1
        e_ab = expected(1234.0, 987.0)
        e_ba = expected(987.0, 1234.0)
        assert e_ab + e_ba == pytest.approx(1.0)


class TestUpdate:
    def test_symmetric_zero_sum(self) -> None:
        new_s, new_q = update(1000.0, 1000.0, actual=True, k=32.0)
        # e = 0.5, delta = 32 * (1 - 0.5) = 16
        assert new_s == pytest.approx(1016.0)
        assert new_q == pytest.approx(984.0)
        # Check zero-sum.
        assert (new_s - 1000.0) + (new_q - 1000.0) == pytest.approx(0.0)

    def test_wrong_reverses_direction(self) -> None:
        new_s, new_q = update(1000.0, 1000.0, actual=False, k=32.0)
        assert new_s == pytest.approx(984.0)
        assert new_q == pytest.approx(1016.0)

    def test_small_surprise_small_delta(self) -> None:
        # Student 1200 vs question 1000, gets it right → E ≈ 0.7597
        # delta = 32 * (1 - 0.7597) = 32 * 0.2403 = 7.6885
        new_s, _ = update(1200.0, 1000.0, actual=True, k=32.0)
        assert new_s - 1200.0 == pytest.approx(32.0 * (1.0 - 0.7597469266479578))

    def test_large_surprise_large_delta(self) -> None:
        # Student 800 vs question 1000, gets it right → E ≈ 0.2403
        # delta = 32 * (1 - 0.2403) = 32 * 0.7597 ≈ 24.31
        new_s, _ = update(800.0, 1000.0, actual=True, k=32.0)
        assert new_s - 800.0 == pytest.approx(32.0 * (1.0 - 0.24025307335204222))


class TestKFactor:
    def test_zero_attempts_is_max(self) -> None:
        assert k_factor(0) == pytest.approx(40.0)

    def test_negative_attempts_is_max(self) -> None:
        assert k_factor(-5) == pytest.approx(40.0)

    def test_midpoint_linear(self) -> None:
        # Attempt 15 of 30 → midway between 40 and 10 = 25.
        assert k_factor(15) == pytest.approx(25.0)

    def test_anneal_end_is_min(self) -> None:
        assert k_factor(30) == pytest.approx(10.0)

    def test_after_end_held_at_min(self) -> None:
        assert k_factor(100) == pytest.approx(10.0)

    def test_monotonic_decreasing(self) -> None:
        values = [k_factor(n) for n in range(0, 35)]
        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1]
