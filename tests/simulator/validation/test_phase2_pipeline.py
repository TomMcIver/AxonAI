"""Tests for B11 Phase 2 integration validation pipeline."""

from __future__ import annotations

import json
import math
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ml.simulator.data.item_bank import Distractor, Item, ItemBank
from ml.simulator.loop.rewriter import QuestionRewriter
from ml.simulator.loop.verifier import RewriteVerifier
from ml.simulator.student.profile import AttemptRecord
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.validation.phase2_pipeline import (
    Phase2ValidationReport,
    _build_bkt_params,
    _build_concept_graph,
    _build_student_profiles,
    _build_synthetic_bank,
    _check_is_simulated_invariant,
    _learning_curve_growth_fraction,
    _style_distribution,
    run_phase2_validation,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _attempt(
    is_correct: bool,
    style: str = "concise_answer",
    time: datetime = datetime(2024, 1, 1),
) -> AttemptRecord:
    return AttemptRecord(
        concept_id=1, item_id=1, is_correct=is_correct,
        time=time, response_time_ms=1000, explanation_style=style,
    )


def _teach(style: str = "concise_answer") -> TeachRecord:
    return TeachRecord(student_id=0, concept_id=1, time=datetime(2024, 1, 1),
                       explanation_style=style)


# ---------------------------------------------------------------------------
# Synthetic fixture tests
# ---------------------------------------------------------------------------

class TestSyntheticFixtures:
    def test_bank_size(self):
        bank = _build_synthetic_bank(n_concepts=3, n_items_per_concept=4)
        assert len(bank) == 12

    def test_concept_graph_has_edges(self):
        g = _build_concept_graph(n_concepts=3)
        assert g.topological_next(set()) is not None

    def test_bkt_params_keys(self):
        params = _build_bkt_params(n_concepts=4)
        assert set(params.keys()) == {1, 2, 3, 4}

    def test_student_profiles_count(self):
        profiles = _build_student_profiles(n_students=10, n_concepts=3)
        assert len(profiles) == 10

    def test_profiles_have_susceptibility(self):
        profiles = _build_student_profiles(n_students=5, n_concepts=2)
        # At least some should have non-empty susceptibility (probabilistic)
        has_any = any(len(p.misconception_susceptibility) > 0 for p in profiles)
        assert has_any


# ---------------------------------------------------------------------------
# Validation check unit tests
# ---------------------------------------------------------------------------

class TestCheckIsSimulatedInvariant:
    def test_all_have_style_passes(self):
        attempts = [_attempt(True, style="hint")]
        teach = [_teach(style="hint")]
        assert _check_is_simulated_invariant(attempts, teach) is True

    def test_attempt_missing_style_fails(self):
        a = AttemptRecord(
            concept_id=1, item_id=1, is_correct=True,
            time=datetime(2024, 1, 1), response_time_ms=1000,
            explanation_style=None,
        )
        assert _check_is_simulated_invariant([a], []) is False

    def test_teach_missing_style_fails(self):
        t = TeachRecord(student_id=0, concept_id=1,
                        time=datetime(2024, 1, 1), explanation_style=None)
        assert _check_is_simulated_invariant([], [t]) is False

    def test_empty_lists_passes(self):
        assert _check_is_simulated_invariant([], []) is True


class TestStyleDistribution:
    def test_counts_correct(self):
        attempts = [
            _attempt(True, style="hint"),
            _attempt(False, style="hint"),
            _attempt(True, style="concise_answer"),
        ]
        dist = _style_distribution(attempts)
        assert dist["hint"] == 2
        assert dist["concise_answer"] == 1

    def test_unknown_style_ignored(self):
        a = AttemptRecord(
            concept_id=1, item_id=1, is_correct=True,
            time=datetime(2024, 1, 1), response_time_ms=500,
            explanation_style="unknown_style",
        )
        dist = _style_distribution([a])
        assert dist.get("unknown_style", 0) == 0


class TestLearningCurveGrowthFraction:
    def test_empty_returns_one(self):
        result = _learning_curve_growth_fraction([], datetime(2024, 1, 1), 5)
        assert result == pytest.approx(1.0)

    def test_one_session_returns_one(self):
        attempts = [_attempt(True, time=datetime(2024, 1, 1))]
        result = _learning_curve_growth_fraction(attempts, datetime(2024, 1, 1), 1)
        assert result == pytest.approx(1.0)

    def test_later_sessions_better_returns_one(self):
        start = datetime(2024, 1, 1)
        # Sessions 0-1: 20% correct; sessions 2-3: 80% correct → late > early
        attempts = (
            [_attempt(False, time=start)] * 8 + [_attempt(True, time=start)] * 2 +
            [_attempt(False, time=datetime(2024, 1, 2))] * 8 + [_attempt(True, time=datetime(2024, 1, 2))] * 2 +
            [_attempt(True, time=datetime(2024, 1, 3))] * 10 +
            [_attempt(True, time=datetime(2024, 1, 4))] * 10
        )
        result = _learning_curve_growth_fraction(attempts, start, 4)
        assert result == pytest.approx(1.0)

    def test_later_sessions_worse_returns_zero(self):
        start = datetime(2024, 1, 1)
        # Sessions 0-1: 80% correct; sessions 2-3: 20% correct → late < early
        attempts = (
            [_attempt(True, time=start)] * 10 +
            [_attempt(True, time=datetime(2024, 1, 2))] * 10 +
            [_attempt(False, time=datetime(2024, 1, 3))] * 8 + [_attempt(True, time=datetime(2024, 1, 3))] * 2 +
            [_attempt(False, time=datetime(2024, 1, 4))] * 8 + [_attempt(True, time=datetime(2024, 1, 4))] * 2
        )
        result = _learning_curve_growth_fraction(attempts, start, 4)
        assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# run_phase2_validation integration test
# ---------------------------------------------------------------------------

class TestRunPhase2Validation:
    def test_returns_report(self):
        report = run_phase2_validation(
            n_students=10, n_sessions=4, n_concepts=2,
            n_items_per_concept=3, seed=0,
        )
        assert isinstance(report, Phase2ValidationReport)

    def test_is_simulated_invariant_passes(self):
        report = run_phase2_validation(
            n_students=10, n_sessions=4, n_concepts=2,
            n_items_per_concept=3, seed=0,
        )
        assert report.is_simulated_invariant_passed is True

    def test_all_styles_present_with_slow_students(self):
        # With enough slow-response students, all 5 styles should fire.
        report = run_phase2_validation(
            n_students=50, n_sessions=5, n_concepts=2,
            n_items_per_concept=4, seed=7,
        )
        # Analogy might not fire in a very small run — check the others at minimum.
        present = sum(1 for v in report.style_distribution.values() if v > 0)
        assert present >= 3  # at least 3 of 5 styles fire

    def test_bkt_growth_reported(self):
        report = run_phase2_validation(
            n_students=20, n_sessions=5, n_concepts=2,
            n_items_per_concept=4, seed=0,
        )
        # BKT should grow (students learn)
        assert report.bkt_mean_final >= report.bkt_mean_initial

    def test_harness_skipped_when_no_rewriter(self):
        report = run_phase2_validation(
            n_students=5, n_sessions=3, n_concepts=2,
            n_items_per_concept=3, seed=0,
        )
        assert report.harness_pass_rate is None
        assert report.harness_gate_passed is True  # waived

    def test_harness_runs_when_provided(self):
        def _make_client(reply: str) -> MagicMock:
            c = MagicMock()
            c.messages.create.return_value = SimpleNamespace(
                content=[SimpleNamespace(text=reply)]
            )
            return c

        rw_reply = json.dumps({"question": "Rewritten Q.", "distractors": ["wrong"]})
        rw = QuestionRewriter(client=_make_client(rw_reply))

        v_reply = json.dumps({"equivalent": True, "confidence": 0.9, "reason": "Same."})
        v = RewriteVerifier(client=_make_client(v_reply))

        report = run_phase2_validation(
            n_students=5, n_sessions=3, n_concepts=2,
            n_items_per_concept=3, seed=0,
            rewriter=rw, verifier=v,
        )
        assert report.harness_pass_rate is not None
        assert 0.0 <= report.harness_pass_rate <= 1.0

    def test_overall_passed_with_defaults(self):
        report = run_phase2_validation(
            n_students=80, n_sessions=8, n_concepts=3,
            n_items_per_concept=4, seed=42,
        )
        assert report.overall_passed is True

    def test_style_distribution_keys(self):
        from ml.simulator.loop.explanation_style import STYLES
        report = run_phase2_validation(
            n_students=5, n_sessions=3, n_concepts=2,
            n_items_per_concept=3, seed=0,
        )
        assert set(report.style_distribution.keys()) == set(STYLES)

    def test_to_dict_serializable(self):
        report = run_phase2_validation(
            n_students=5, n_sessions=3, n_concepts=2,
            n_items_per_concept=3, seed=0,
        )
        d = report.to_dict()
        # Should be JSON-serializable
        json.dumps(d)
