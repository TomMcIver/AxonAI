"""Tests for TermRunner.

End-to-end at small scale: a chain of 3 concepts, a couple of items per
concept, short term. We verify the event stream shape, mastery
progression, that time advances, and that the student learns (correct
rate rises).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import networkx as nx
import numpy as np
import pytest

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.loop.revise import ReviseRecord
from ml.simulator.loop.runner import SessionEndRecord, TermRunner
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.profile import AttemptRecord, StudentProfile


def _graph() -> ConceptGraph:
    g = nx.DiGraph()
    g.add_edges_from([(1, 2), (2, 3)])
    return ConceptGraph(g)


def _bank() -> ItemBank:
    items = []
    for concept in (1, 2, 3):
        for k in range(3):
            items.append(
                Item(
                    item_id=concept * 100 + k,
                    concept_id=concept,
                    a=1.2,
                    b=-0.5 + 0.5 * k,
                )
            )
    return ItemBank(items)


def _bkt_params() -> dict[int, BKTParams]:
    return {
        c: BKTParams(p_init=0.2, p_transit=0.2, p_slip=0.08, p_guess=0.2)
        for c in (1, 2, 3)
    }


def _profile() -> StudentProfile:
    return StudentProfile(
        student_id=7,
        true_theta={1: 0.2, 2: 0.0, 3: -0.1},
        estimated_theta={c: (0.0, 1.0) for c in (1, 2, 3)},
        bkt_state={c: BKTState(p_known=0.2) for c in (1, 2, 3)},
        elo_rating=1200.0,
        recall_half_life={c: 24.0 for c in (1, 2, 3)},
        last_retrieval={},
        learning_rate=0.15,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(math.log(8000.0), 0.3),
        attempts_history=[],
    )


class TestTermRunner:
    def test_yields_events_in_expected_shape(self) -> None:
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            n_sessions=2,
            seed=0,
        )
        events = list(runner.run())
        # Each session: TeachRecord, up to QUIZ attempts, optional ReviseRecord + attempts, SessionEndRecord.
        teaches = [e for e in events if isinstance(e, TeachRecord)]
        session_ends = [e for e in events if isinstance(e, SessionEndRecord)]
        attempts = [e for e in events if isinstance(e, AttemptRecord)]
        assert len(session_ends) == 2
        assert len(teaches) >= 1
        assert len(attempts) >= 1

    def test_time_advances_between_sessions(self) -> None:
        start = datetime(2024, 1, 1, 9, 0, 0)
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=start,
            n_sessions=3,
            session_interval_hours=24,
            seed=0,
        )
        events = list(runner.run())
        session_ends = [e for e in events if isinstance(e, SessionEndRecord)]
        assert session_ends[0].time == start
        assert session_ends[1].time == start + timedelta(hours=24)
        assert session_ends[2].time == start + timedelta(hours=48)

    def test_first_teach_is_root_concept(self) -> None:
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1),
            n_sessions=1,
            seed=0,
        )
        events = list(runner.run())
        teaches = [e for e in events if isinstance(e, TeachRecord)]
        assert teaches[0].concept_id == 1

    def test_mastery_progresses_through_chain(self) -> None:
        # Give the student plenty of sessions and an easy starting theta
        # so we eventually advance past concept 1.
        profile = _profile()
        profile.true_theta = {1: 2.5, 2: 2.0, 3: 1.5}  # very capable
        runner = TermRunner(
            student=profile,
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1),
            n_sessions=15,
            quiz_items_per_session=8,
            seed=0,
        )
        events = list(runner.run())
        taught_concepts = {e.concept_id for e in events if isinstance(e, TeachRecord)}
        assert 1 in taught_concepts
        # Expect the runner to advance beyond concept 1.
        assert len(taught_concepts) >= 2

    def test_deterministic_given_seed(self) -> None:
        def run():
            runner = TermRunner(
                student=_profile(),
                concept_graph=_graph(),
                item_bank=_bank(),
                bkt_params_by_concept=_bkt_params(),
                start_time=datetime(2024, 1, 1),
                n_sessions=3,
                seed=123,
            )
            return [
                (type(e).__name__, getattr(e, "concept_id", None),
                 getattr(e, "item_id", None), getattr(e, "is_correct", None))
                for e in runner.run()
            ]
        assert run() == run()

    def test_final_profile_is_stored(self) -> None:
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1),
            n_sessions=2,
            seed=0,
        )
        list(runner.run())
        assert hasattr(runner, "final_profile")
        assert runner.final_profile is not _profile()
        assert len(runner.final_profile.attempts_history) > 0

    def test_student_learns_taught_concept(self) -> None:
        # Under ZPD-adaptive quizzing the correct-rate sits near the band
        # centre regardless of skill, so "students get better" surfaces as
        # rising true theta + BKT mastery, not rising correct rate.
        profile = _profile()
        profile.true_theta = {1: 0.5, 2: 0.5, 3: 0.5}
        starting_theta = profile.true_theta[1]
        runner = TermRunner(
            student=profile,
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1),
            n_sessions=20,
            session_interval_hours=1.0,
            quiz_items_per_session=10,
            seed=1,
        )
        events = list(runner.run())
        attempts = [e for e in events if isinstance(e, AttemptRecord)]
        assert len(attempts) > 20
        final = runner.final_profile
        assert final.true_theta[1] > starting_theta
        assert final.bkt_state[1].p_known > profile.bkt_state[1].p_known

    def test_every_attempt_has_an_explanation_style(self) -> None:
        """B6: the runner must stamp every AttemptRecord with a style."""
        from ml.simulator.loop.explanation_style import STYLES
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            n_sessions=3,
            seed=1,
        )
        events = list(runner.run())
        attempts = [e for e in events if isinstance(e, AttemptRecord)]
        assert attempts
        for a in attempts:
            assert a.explanation_style in STYLES

    def test_initial_attempts_use_worked_example_for_not_learned_concept(self) -> None:
        """BKT p_known starts at 0.2 everywhere → first attempts hit rule 2."""
        from ml.simulator.loop.explanation_style import WORKED_EXAMPLE
        runner = TermRunner(
            student=_profile(),
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            n_sessions=1,
            seed=0,
        )
        events = list(runner.run())
        attempts = [e for e in events if isinstance(e, AttemptRecord)]
        assert attempts
        # The very first attempt on the first quizzed concept starts
        # with BKT p_known = 0.2 < 0.4 threshold.
        assert attempts[0].explanation_style == WORKED_EXAMPLE

    def test_revise_record_emitted_once_candidates_exist(self) -> None:
        # Run long enough for earlier concepts to slide into the HLR band.
        profile = _profile()
        profile.true_theta = {1: 1.5, 2: 1.5, 3: 1.5}
        runner = TermRunner(
            student=profile,
            concept_graph=_graph(),
            item_bank=_bank(),
            bkt_params_by_concept=_bkt_params(),
            start_time=datetime(2024, 1, 1),
            n_sessions=10,
            session_interval_hours=24,
            quiz_items_per_session=6,
            seed=0,
        )
        events = list(runner.run())
        revise_records = [e for e in events if isinstance(e, ReviseRecord)]
        assert len(revise_records) >= 1
