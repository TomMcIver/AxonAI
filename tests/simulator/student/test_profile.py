"""Tests for the StudentProfile dataclass."""

from __future__ import annotations

from datetime import datetime

from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import AttemptRecord, StudentProfile


def _make_profile() -> StudentProfile:
    return StudentProfile(
        student_id=1,
        true_theta={1: 0.5, 2: -0.2},
        estimated_theta={1: (0.0, 1.0), 2: (0.0, 1.0)},
        bkt_state={1: BKTState(p_known=0.2), 2: BKTState(p_known=0.2)},
        elo_rating=1200.0,
        recall_half_life={1: 24.0, 2: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
    )


class TestStudentProfile:
    def test_defaults_history_empty(self) -> None:
        p = _make_profile()
        assert p.attempts_history == []
        assert p.misconception_susceptibility == {}

    def test_attempts_on_total(self) -> None:
        p = _make_profile()
        p.attempts_history.append(
            AttemptRecord(
                concept_id=1,
                item_id=10,
                is_correct=True,
                time=datetime(2024, 1, 1),
                response_time_ms=5000,
            )
        )
        p.attempts_history.append(
            AttemptRecord(
                concept_id=2,
                item_id=11,
                is_correct=False,
                time=datetime(2024, 1, 1),
                response_time_ms=7000,
            )
        )
        assert p.attempts_on() == 2
        assert p.attempts_on(1) == 1
        assert p.attempts_on(99) == 0

    def test_attempt_record_frozen(self) -> None:
        record = AttemptRecord(
            concept_id=1,
            item_id=10,
            is_correct=True,
            time=datetime(2024, 1, 1),
            response_time_ms=5000,
        )
        try:
            record.concept_id = 2  # type: ignore[misc]
        except Exception:
            return
        raise AssertionError("AttemptRecord should be frozen")
