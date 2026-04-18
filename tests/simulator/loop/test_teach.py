"""Tests for loop.teach."""

from __future__ import annotations

from datetime import datetime

from ml.simulator.loop.teach import TeachRecord, teach
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


def _profile() -> StudentProfile:
    return StudentProfile(
        student_id=5,
        true_theta={1: 0.0, 2: 0.1},
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
        attempts_history=[],
    )


class TestTeach:
    def test_sets_last_retrieval_on_concept(self) -> None:
        p = _profile()
        now = datetime(2024, 1, 1, 9, 0, 0)
        new_p, record = teach(p, concept_id=2, now=now)
        assert new_p.last_retrieval[2] == now

    def test_does_not_mutate_input(self) -> None:
        p = _profile()
        _ = teach(p, concept_id=1, now=datetime(2024, 1, 1))
        assert p.last_retrieval == {}

    def test_emits_record_with_correct_fields(self) -> None:
        p = _profile()
        now = datetime(2024, 1, 1)
        _, record = teach(p, concept_id=1, now=now)
        assert isinstance(record, TeachRecord)
        assert record.student_id == 5
        assert record.concept_id == 1
        assert record.time == now

    def test_true_theta_unchanged(self) -> None:
        p = _profile()
        now = datetime(2024, 1, 1)
        new_p, _ = teach(p, concept_id=1, now=now)
        assert new_p.true_theta == p.true_theta
