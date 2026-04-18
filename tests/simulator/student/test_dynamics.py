"""Tests for apply_practice and apply_forgetting."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.dynamics import apply_forgetting, apply_practice
from ml.simulator.student.profile import AttemptRecord, StudentProfile


def _make_profile(
    *,
    theta: float = 0.0,
    half_life: float = 24.0,
    elo: float = 1200.0,
    last_retrieval: datetime | None = None,
) -> StudentProfile:
    return StudentProfile(
        student_id=1,
        true_theta={1: theta},
        estimated_theta={1: (0.0, 1.0)},
        bkt_state={1: BKTState(p_known=0.2)},
        elo_rating=elo,
        recall_half_life={1: half_life},
        last_retrieval={1: last_retrieval} if last_retrieval is not None else {},
        learning_rate=0.2,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
        attempts_history=[],
    )


_BKT = BKTParams(p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25)


class TestApplyPractice:
    def test_does_not_mutate_input(self) -> None:
        p = _make_profile()
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        # Originals untouched.
        assert p.true_theta == {1: 0.0}
        assert p.attempts_history == []
        assert p.bkt_state[1].p_known == 0.2
        # Result reflects change.
        assert new_p.true_theta[1] > 0.0
        assert len(new_p.attempts_history) == 1

    def test_correct_bumps_theta_up(self) -> None:
        p = _make_profile(theta=0.0)
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        assert new_p.true_theta[1] == pytest.approx(0.2)  # learning_rate = 0.2

    def test_wrong_bumps_theta_down_by_smaller_magnitude(self) -> None:
        p = _make_profile(theta=0.0)
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=False,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        # wrong_decay_fraction = 0.5 → delta = -0.5 * 0.2 = -0.1
        assert new_p.true_theta[1] == pytest.approx(-0.1)

    def test_theta_clamped_to_bounds(self) -> None:
        p = _make_profile(theta=3.95)
        p.learning_rate = 1.0  # big bump
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        assert new_p.true_theta[1] == pytest.approx(4.0)

    def test_bkt_state_updates(self) -> None:
        p = _make_profile()
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        # Correct observation: posterior rises; then transition raises it further.
        assert new_p.bkt_state[1].p_known > 0.2

    def test_elo_symmetric_zero_sum(self) -> None:
        p = _make_profile(elo=1200.0)
        now = datetime(2024, 1, 1)
        new_p, new_item_rating = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        student_delta = new_p.elo_rating - 1200.0
        item_delta = new_item_rating - 1200.0
        assert student_delta == pytest.approx(-item_delta)
        assert student_delta > 0.0  # student won

    def test_half_life_grows_on_correct(self) -> None:
        p = _make_profile(half_life=24.0)
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        assert new_p.recall_half_life[1] == pytest.approx(48.0)  # default x2

    def test_half_life_shrinks_on_wrong(self) -> None:
        p = _make_profile(half_life=24.0)
        now = datetime(2024, 1, 1)
        new_p, _ = apply_practice(
            p, item_id=10, concept_id=1, is_correct=False,
            item_rating=1200.0, bkt_params=_BKT, now=now,
        )
        assert new_p.recall_half_life[1] == pytest.approx(12.0)  # default x0.5

    def test_history_and_last_retrieval_recorded(self) -> None:
        p = _make_profile()
        now = datetime(2024, 1, 1, 12, 0, 0)
        new_p, _ = apply_practice(
            p, item_id=42, concept_id=1, is_correct=True,
            item_rating=1200.0, bkt_params=_BKT, now=now,
            response_time_ms=8500,
        )
        assert new_p.last_retrieval[1] == now
        assert len(new_p.attempts_history) == 1
        rec = new_p.attempts_history[0]
        assert rec.item_id == 42
        assert rec.concept_id == 1
        assert rec.is_correct is True
        assert rec.response_time_ms == 8500


class TestApplyForgetting:
    def test_no_op_when_no_last_retrieval(self) -> None:
        p = _make_profile(theta=0.7)
        new_p = apply_forgetting(p, datetime(2024, 1, 2))
        assert new_p.true_theta[1] == 0.7

    def test_decays_theta_toward_floor(self) -> None:
        t0 = datetime(2024, 1, 1)
        p = _make_profile(theta=2.0, half_life=24.0, last_retrieval=t0)
        # 24 hours later: factor = 2^-1 = 0.5
        new_p = apply_forgetting(p, t0 + timedelta(hours=24))
        # floor + (theta - floor) * 0.5 = -2 + (2 - -2) * 0.5 = 0.0
        assert new_p.true_theta[1] == pytest.approx(0.0)

    def test_does_not_mutate_input(self) -> None:
        t0 = datetime(2024, 1, 1)
        p = _make_profile(theta=1.0, last_retrieval=t0)
        _ = apply_forgetting(p, t0 + timedelta(hours=72))
        assert p.true_theta[1] == 1.0

    def test_negative_time_treated_as_zero(self) -> None:
        # now < last_retrieval — shouldn't blow up; factor = 1.
        t0 = datetime(2024, 1, 5)
        p = _make_profile(theta=1.5, last_retrieval=t0)
        new_p = apply_forgetting(p, t0 - timedelta(hours=1))
        assert new_p.true_theta[1] == pytest.approx(1.5)

    def test_leaves_half_life_untouched(self) -> None:
        t0 = datetime(2024, 1, 1)
        p = _make_profile(theta=1.0, half_life=24.0, last_retrieval=t0)
        new_p = apply_forgetting(p, t0 + timedelta(hours=100))
        assert new_p.recall_half_life[1] == 24.0

    def test_leaves_last_retrieval_untouched(self) -> None:
        t0 = datetime(2024, 1, 1)
        p = _make_profile(theta=1.0, last_retrieval=t0)
        new_p = apply_forgetting(p, t0 + timedelta(hours=48))
        assert new_p.last_retrieval[1] == t0
