"""Tests for the B5 MisconceptionDetector loop integration."""

from __future__ import annotations

import pytest

from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.loop.explanation_style import DetectorHint
from ml.simulator.misconception.detector import MisconceptionDetector, _MIN_SUSCEPTIBILITY_FOR_HINT
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


def _profile(susceptibility: dict[int, float] | None = None) -> StudentProfile:
    return StudentProfile(
        student_id=0,
        true_theta={1: 0.0},
        estimated_theta={1: (0.0, 1.0)},
        bkt_state={1: BKTState(p_known=0.5)},
        elo_rating=1200.0,
        recall_half_life={1: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
        misconception_susceptibility=susceptibility or {},
    )


def _item(*misconception_ids: int | None) -> Item:
    return Item(
        item_id=1,
        concept_id=1,
        a=1.0,
        b=0.0,
        distractors=tuple(
            Distractor(option_text=f"opt{i}", misconception_id=mid)
            for i, mid in enumerate(misconception_ids)
        ),
    )


def _bare_item() -> Item:
    return Item(item_id=2, concept_id=1, a=1.0, b=0.0)


class TestTaggedShortcut:
    def test_returns_none_when_no_distractors(self):
        d = MisconceptionDetector()
        assert d.predict(_profile({10: 0.8}), _bare_item()) is None

    def test_returns_none_when_no_susceptibility_match(self):
        d = MisconceptionDetector()
        p = _profile({99: 0.8})  # susceptibility for unrelated misconception
        item = _item(10, 20)  # tagged with 10 and 20
        assert d.predict(p, item) is None

    def test_returns_hint_for_matched_misconception(self):
        d = MisconceptionDetector()
        p = _profile({10: 0.7})
        item = _item(10)
        hint = d.predict(p, item)
        assert hint is not None
        assert hint.misconception_id == 10
        assert hint.confidence == pytest.approx(0.7)

    def test_returns_highest_susceptibility(self):
        d = MisconceptionDetector()
        p = _profile({10: 0.3, 20: 0.8, 30: 0.5})
        item = _item(10, 20, 30)
        hint = d.predict(p, item)
        assert hint is not None
        assert hint.misconception_id == 20
        assert hint.confidence == pytest.approx(0.8)

    def test_skips_untagged_distractors(self):
        d = MisconceptionDetector()
        p = _profile({10: 0.6})
        item = _item(None, 10)  # first distractor has no tag
        hint = d.predict(p, item)
        assert hint is not None
        assert hint.misconception_id == 10

    def test_below_min_susceptibility_returns_none(self):
        d = MisconceptionDetector(min_susceptibility=0.5)
        p = _profile({10: 0.3})  # below threshold
        item = _item(10)
        assert d.predict(p, item) is None

    def test_returns_none_when_all_susceptibility_zero(self):
        d = MisconceptionDetector()
        p = _profile()  # empty susceptibility
        item = _item(10, 20)
        assert d.predict(p, item) is None

    def test_disabled_shortcut_with_no_index_returns_none(self):
        d = MisconceptionDetector(use_tagged_shortcut=False)
        p = _profile({10: 0.8})
        item = _item(10)
        # shortcut disabled, no retrieval_index → None
        assert d.predict(p, item) is None

    def test_returns_detector_hint_type(self):
        d = MisconceptionDetector()
        p = _profile({10: 0.8})
        item = _item(10)
        hint = d.predict(p, item)
        assert isinstance(hint, DetectorHint)


class TestRunnerIntegration:
    """Integration: TermRunner with a MisconceptionDetector fires Rule 1."""

    def test_runner_accepts_detector_field(self):
        import math
        import networkx as nx
        import numpy as np
        from datetime import datetime
        from ml.simulator.data.concept_graph import ConceptGraph
        from ml.simulator.data.item_bank import ItemBank
        from ml.simulator.loop.runner import TermRunner
        from ml.simulator.psychometrics.bkt import BKTParams, BKTState
        from ml.simulator.student.profile import AttemptRecord, StudentProfile
        from ml.simulator.loop.explanation_style import CONTRAST_WITH_MISCONCEPTION

        g = nx.DiGraph()
        g.add_edge(1, 2)
        concept_graph = ConceptGraph(g)

        # Item tagged with misconception 42.
        item = Item(
            item_id=101, concept_id=1, a=1.0, b=-0.5,
            distractors=(Distractor(option_text="wrong", misconception_id=42),),
        )
        bank = ItemBank([item])
        bkt = {1: BKTParams(0.2, 0.1, 0.08, 0.2), 2: BKTParams(0.2, 0.1, 0.08, 0.2)}

        profile = StudentProfile(
            student_id=0,
            true_theta={1: -2.0, 2: -2.0},  # low ability → likely wrong
            estimated_theta={1: (0.0, 1.0), 2: (0.0, 1.0)},
            bkt_state={c: BKTState(p_known=0.2) for c in (1, 2)},
            elo_rating=1200.0,
            recall_half_life={1: 24.0, 2: 24.0},
            last_retrieval={},
            learning_rate=0.1,
            slip=0.1,
            guess=0.05,
            engagement_decay=0.95,
            response_time_lognorm_params=(math.log(8000), 0.3),
            misconception_susceptibility={42: 0.9},  # high susceptibility
        )

        detector = MisconceptionDetector()
        runner = TermRunner(
            student=profile,
            concept_graph=concept_graph,
            item_bank=bank,
            bkt_params_by_concept=bkt,
            start_time=datetime(2024, 1, 1),
            n_sessions=1,
            seed=0,
            misconception_detector=detector,
        )
        events = list(runner.run())
        attempts = [e for e in events if isinstance(e, AttemptRecord)]
        # All attempts should have explanation_style = contrast_with_misconception
        # because susceptibility=0.9 ≥ 0.6 threshold.
        assert attempts
        for a in attempts:
            assert a.explanation_style == CONTRAST_WITH_MISCONCEPTION
