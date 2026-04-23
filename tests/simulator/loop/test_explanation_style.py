"""Tests for the B6 explanation-style selector.

Covers each of the five rules, the first-match-wins tie-break across
every pair that can simultaneously fire, default fallback, and
determinism (same inputs → same string).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ml.simulator.loop.explanation_style import (
    ANALOGY,
    CONCISE_ANSWER,
    CONTRAST_WITH_MISCONCEPTION,
    DetectorHint,
    ExplanationStyleConfig,
    HINT,
    STYLES,
    WORKED_EXAMPLE,
    select_explanation_style,
)
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import AttemptRecord, StudentProfile


def _profile(
    *,
    p_known: float = 0.9,
    history: list[AttemptRecord] | None = None,
    concept_id: int = 1,
) -> StudentProfile:
    return StudentProfile(
        student_id=0,
        true_theta={concept_id: 0.0},
        estimated_theta={concept_id: (0.0, 1.0)},
        bkt_state={concept_id: BKTState(p_known=p_known)},
        elo_rating=1200.0,
        recall_half_life={concept_id: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
        attempts_history=history or [],
    )


def _attempt(
    concept_id: int,
    *,
    correct: bool,
    rt_ms: int = 5_000,
    when: datetime | None = None,
) -> AttemptRecord:
    return AttemptRecord(
        concept_id=concept_id,
        item_id=1,
        is_correct=correct,
        time=when or datetime(2024, 1, 1),
        response_time_ms=rt_ms,
    )


class TestRule1Misconception:
    def test_high_confidence_hint_triggers(self):
        p = _profile(p_known=0.9)
        hint = DetectorHint(misconception_id=42, confidence=0.75)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONTRAST_WITH_MISCONCEPTION

    def test_threshold_exact_match_triggers(self):
        """>= semantics: confidence == threshold fires rule 1."""
        p = _profile(p_known=0.9)
        hint = DetectorHint(misconception_id=42, confidence=0.6)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONTRAST_WITH_MISCONCEPTION

    def test_below_threshold_does_not_trigger(self):
        p = _profile(p_known=0.9)
        hint = DetectorHint(misconception_id=42, confidence=0.59)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONCISE_ANSWER

    def test_none_detector_hint_falls_through(self):
        p = _profile(p_known=0.9)
        assert select_explanation_style(p, 1, detector_hint=None) == CONCISE_ANSWER


class TestRule2WorkedExample:
    def test_low_p_known_triggers(self):
        p = _profile(p_known=0.2)
        assert select_explanation_style(p, 1) == WORKED_EXAMPLE

    def test_at_threshold_does_not_trigger(self):
        """Strict < semantics: p_known == not_learned_threshold falls through."""
        cfg = ExplanationStyleConfig()
        p = _profile(p_known=cfg.not_learned_threshold)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER

    def test_missing_concept_falls_through(self):
        """No BKT state for the concept → skip rule 2 (don't crash)."""
        p = _profile(p_known=0.9, concept_id=1)
        # Ask about a concept not in bkt_state.
        assert select_explanation_style(p, 999) == CONCISE_ANSWER


class TestRule3Hint:
    def test_two_wrong_in_a_row_triggers(self):
        history = [
            _attempt(1, correct=True),
            _attempt(1, correct=False),
            _attempt(1, correct=False),
        ]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == HINT

    def test_wrong_then_right_does_not_trigger(self):
        history = [
            _attempt(1, correct=False),
            _attempt(1, correct=True),
        ]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER

    def test_only_one_wrong_does_not_trigger(self):
        history = [_attempt(1, correct=False)]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER

    def test_wrong_streak_on_other_concept_does_not_trigger(self):
        history = [
            _attempt(99, correct=False),
            _attempt(99, correct=False),
        ]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER


class TestRule4Analogy:
    def test_slow_recent_attempt_triggers(self):
        history = [_attempt(1, correct=True, rt_ms=45_000)]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == ANALOGY

    def test_fast_recent_attempt_does_not_trigger(self):
        history = [_attempt(1, correct=True, rt_ms=5_000)]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER

    def test_uses_only_most_recent_on_concept(self):
        """Looks at the most-recent attempt on this concept, not globally."""
        history = [
            _attempt(1, correct=True, rt_ms=45_000, when=datetime(2024, 1, 1)),
            _attempt(2, correct=True, rt_ms=1_000, when=datetime(2024, 1, 2)),
        ]
        p = _profile(p_known=0.9, history=history)
        # Asking about concept 1 — the only concept-1 attempt was slow.
        assert select_explanation_style(p, 1) == ANALOGY
        # Asking about concept 2 — fast.
        # But concept 2 has no BKT state in the fixture profile, so rule
        # 2's "missing concept falls through" semantics apply.
        assert select_explanation_style(p, 2) == CONCISE_ANSWER


class TestRule5Default:
    def test_well_calibrated_student_gets_concise(self):
        p = _profile(p_known=0.9)
        assert select_explanation_style(p, 1) == CONCISE_ANSWER

    def test_return_value_is_in_style_vocabulary(self):
        p = _profile(p_known=0.9)
        assert select_explanation_style(p, 1) in STYLES


class TestFirstMatchWinsOrdering:
    """The plan document locked in first-match-wins explicitly."""

    def test_rule1_beats_rule2(self):
        """Misconception + not-learned → rule 1."""
        p = _profile(p_known=0.2)
        hint = DetectorHint(misconception_id=42, confidence=0.9)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONTRAST_WITH_MISCONCEPTION

    def test_rule1_beats_rule3(self):
        """Misconception + wrong streak → rule 1."""
        history = [_attempt(1, correct=False), _attempt(1, correct=False)]
        p = _profile(p_known=0.9, history=history)
        hint = DetectorHint(misconception_id=42, confidence=0.9)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONTRAST_WITH_MISCONCEPTION

    def test_rule1_beats_rule4(self):
        """Misconception + slow last attempt → rule 1."""
        history = [_attempt(1, correct=True, rt_ms=60_000)]
        p = _profile(p_known=0.9, history=history)
        hint = DetectorHint(misconception_id=42, confidence=0.9)
        assert select_explanation_style(p, 1, detector_hint=hint) == CONTRAST_WITH_MISCONCEPTION

    def test_rule2_beats_rule3(self):
        """Not-learned + wrong streak → worked example, not hint."""
        history = [_attempt(1, correct=False), _attempt(1, correct=False)]
        p = _profile(p_known=0.1, history=history)
        assert select_explanation_style(p, 1) == WORKED_EXAMPLE

    def test_rule2_beats_rule4(self):
        """Not-learned + slow → worked example."""
        history = [_attempt(1, correct=True, rt_ms=60_000)]
        p = _profile(p_known=0.1, history=history)
        assert select_explanation_style(p, 1) == WORKED_EXAMPLE

    def test_rule3_beats_rule4(self):
        """Wrong streak (with last one slow) → hint, not analogy."""
        history = [
            _attempt(1, correct=False, rt_ms=60_000),
            _attempt(1, correct=False, rt_ms=60_000),
        ]
        p = _profile(p_known=0.9, history=history)
        assert select_explanation_style(p, 1) == HINT


class TestConfigOverride:
    def test_respects_custom_confidence_threshold(self):
        p = _profile(p_known=0.9)
        hint = DetectorHint(misconception_id=42, confidence=0.5)
        # Default 0.6 → falls through.
        assert select_explanation_style(p, 1, detector_hint=hint) == CONCISE_ANSWER
        # Lower threshold → triggers.
        cfg = ExplanationStyleConfig(misconception_confidence_threshold=0.4)
        assert (
            select_explanation_style(p, 1, detector_hint=hint, config=cfg)
            == CONTRAST_WITH_MISCONCEPTION
        )

    def test_respects_custom_streak_threshold(self):
        history = [_attempt(1, correct=False)]
        p = _profile(p_known=0.9, history=history)
        # Default 2 → one wrong alone doesn't fire.
        assert select_explanation_style(p, 1) == CONCISE_ANSWER
        # Lower streak → triggers on one.
        cfg = ExplanationStyleConfig(streak_wrong_threshold=1)
        assert select_explanation_style(p, 1, config=cfg) == HINT


class TestDeterminism:
    def test_pure_function(self):
        p = _profile(p_known=0.2)
        a = select_explanation_style(p, 1)
        b = select_explanation_style(p, 1)
        assert a == b
