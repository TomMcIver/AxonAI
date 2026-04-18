"""Tests for loop.revise."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ml.simulator.loop.revise import select_revision_concepts
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


def _profile(last_retrieval: dict, half_lives: dict) -> StudentProfile:
    concepts = set(last_retrieval) | set(half_lives)
    return StudentProfile(
        student_id=1,
        true_theta={c: 0.0 for c in concepts},
        estimated_theta={c: (0.0, 1.0) for c in concepts},
        bkt_state={c: BKTState(p_known=0.2) for c in concepts},
        elo_rating=1200.0,
        recall_half_life=half_lives,
        last_retrieval=last_retrieval,
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
        attempts_history=[],
    )


class TestSelectRevisionConcepts:
    def test_returns_in_band_concepts(self) -> None:
        # Concept 1: 24h since, hl=24 → recall = 0.5 (in band)
        # Concept 2: 72h since, hl=24 → recall = 0.125 (too low)
        # Concept 3: 1h since,  hl=24 → recall ~ 0.97 (too high)
        t0 = datetime(2024, 1, 5, 12, 0, 0)
        p = _profile(
            last_retrieval={
                1: t0 - timedelta(hours=24),
                2: t0 - timedelta(hours=72),
                3: t0 - timedelta(hours=1),
            },
            half_lives={1: 24.0, 2: 24.0, 3: 24.0},
        )
        out = select_revision_concepts(p, t0)
        assert out == [1]

    def test_sorted_weakest_first(self) -> None:
        # Two concepts in band, different recall levels.
        t0 = datetime(2024, 1, 5)
        p = _profile(
            last_retrieval={
                1: t0 - timedelta(hours=18),  # recall = 2^-0.75 ~ 0.59 (in band)
                2: t0 - timedelta(hours=12),  # recall = 2^-0.5 ~ 0.71 (just above band max=0.70)
                3: t0 - timedelta(hours=21),  # recall ~ 0.54 (in band)
            },
            half_lives={1: 24.0, 2: 24.0, 3: 24.0},
        )
        out = select_revision_concepts(p, t0)
        # 3 is weaker (lower recall) than 1, so it should come first.
        assert out == [3, 1]

    def test_caps_at_max_concepts(self) -> None:
        t0 = datetime(2024, 1, 5)
        # All 12 concepts sit smack in the middle of the band.
        n = 12
        last = {c: t0 - timedelta(hours=24) for c in range(n)}
        hls = {c: 24.0 for c in range(n)}
        p = _profile(last, hls)
        out = select_revision_concepts(p, t0, max_concepts=5)
        assert len(out) == 5

    def test_excludes_concepts_without_retrieval(self) -> None:
        t0 = datetime(2024, 1, 5)
        p = _profile(last_retrieval={}, half_lives={1: 24.0, 2: 24.0})
        assert select_revision_concepts(p, t0) == []

    def test_custom_band(self) -> None:
        t0 = datetime(2024, 1, 5)
        # recall = 0.5 exactly.
        p = _profile(
            last_retrieval={1: t0 - timedelta(hours=24)},
            half_lives={1: 24.0},
        )
        # Band [0.6, 0.8] excludes it.
        assert select_revision_concepts(p, t0, min_recall=0.6, max_recall=0.8) == []
        # Band [0.3, 0.6] includes it.
        assert select_revision_concepts(p, t0, min_recall=0.3, max_recall=0.6) == [1]
