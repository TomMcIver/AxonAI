"""PR-1.5 — tests for SimulationConfig feature toggles.

Four scenarios:
    1. YAML parse: phase_2_validation.yaml → every toggle surfaces correctly.
    2. Smoke — all toggles on: 10 students × 1 week with detector + tutor +
       misconception_weighted response model. Pipeline completes.
    3. Smoke — detector off: runner emits attempts, but no attempt is framed
       with the `contrast_with_misconception` style (Rule 1 needs the hint).
    4. Smoke — tutor off: every TeachRecord has `llm_explanation=None` and
       the injected mock tutor client's `generate_explanation` is never
       called.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ml.simulator.config import SimulationConfig
from ml.simulator.loop.llm_tutor import LLMTutor
from ml.simulator.loop.runner import TermRunner
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.student.profile import AttemptRecord
from ml.simulator.validation.phase2_pipeline import (
    _build_bkt_params,
    _build_concept_graph,
    _build_student_profiles,
    _build_synthetic_bank,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _smoke_runner(
    *,
    detector_enabled: bool,
    tutor_enabled: bool,
    response_model: str,
    seed: int = 42,
) -> tuple[TermRunner, MagicMock | None]:
    """Build a 10-student × 3-session runner honouring the given toggles.

    Returns the runner plus the mock tutor client (or None when tutor_enabled
    is False) so the caller can assert call counts.
    """
    bank = _build_synthetic_bank(n_concepts=2, n_items_per_concept=4, seed=seed)
    graph = _build_concept_graph(n_concepts=2)
    bkt_params = _build_bkt_params(n_concepts=2)
    profiles = _build_student_profiles(n_students=10, n_concepts=2, seed=seed)

    detector = MisconceptionDetector() if detector_enabled else None

    tutor: LLMTutor | None = None
    mock_client: MagicMock | None = None
    if tutor_enabled:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="stub explanation")]
        )
        tutor = LLMTutor(client=mock_client)

    # One runner per student — return the first for the caller to `.run()`,
    # but attach the cohort list + shared state so callers can iterate.
    runner = TermRunner(
        student=profiles[0],
        concept_graph=graph,
        item_bank=bank,
        bkt_params_by_concept=bkt_params,
        start_time=datetime(2024, 1, 1),
        n_sessions=3,
        seed=seed,
        misconception_detector=detector,
        llm_tutor=tutor,
        response_model=response_model,
    )
    # Stash for multi-student smoke runs.
    runner._cohort = profiles  # type: ignore[attr-defined]
    return runner, mock_client


def _drain_cohort(runner: TermRunner) -> tuple[list[AttemptRecord], list[TeachRecord]]:
    """Run every student in runner._cohort; collect attempts + teach records."""
    attempts: list[AttemptRecord] = []
    teaches: list[TeachRecord] = []
    for profile in runner._cohort:  # type: ignore[attr-defined]
        r = TermRunner(
            student=profile,
            concept_graph=runner.concept_graph,
            item_bank=runner.item_bank,
            bkt_params_by_concept=runner.bkt_params_by_concept,
            start_time=runner.start_time,
            n_sessions=runner.n_sessions,
            seed=runner.seed,
            misconception_detector=runner.misconception_detector,
            llm_tutor=runner.llm_tutor,
            response_model=runner.response_model,
        )
        for event in r.run():
            if isinstance(event, AttemptRecord):
                attempts.append(event)
            elif isinstance(event, TeachRecord):
                teaches.append(event)
    return attempts, teaches


# ---------------------------------------------------------------------------
# 1. YAML parsing
# ---------------------------------------------------------------------------

class TestPhase2ValidationYaml:
    def test_all_toggles_parse(self) -> None:
        cfg = SimulationConfig.from_yaml(
            Path("ml/simulator/configs/phase_2_validation.yaml")
        )
        assert cfg.n_students == 500
        assert cfg.term_weeks == 12
        assert cfg.sessions_per_week == 5
        assert cfg.minutes_per_session == 45
        assert cfg.seed == 42
        assert cfg.output_target == "postgres"
        assert cfg.detector_enabled is True
        assert cfg.tutor_enabled is True
        assert cfg.rewriter_enabled is True
        assert cfg.response_model == "misconception_weighted"


# ---------------------------------------------------------------------------
# 2. Smoke — all toggles on
# ---------------------------------------------------------------------------

class TestAllTogglesOn:
    def test_pipeline_completes(self) -> None:
        runner, _ = _smoke_runner(
            detector_enabled=True,
            tutor_enabled=True,
            response_model="misconception_weighted",
        )
        attempts, teaches = _drain_cohort(runner)
        assert len(attempts) > 0
        assert len(teaches) > 0
        # Every record carries the literal is_simulated=True field (PR-1.75b).
        assert all(a.is_simulated is True for a in attempts)
        assert all(t.is_simulated is True for t in teaches)


# ---------------------------------------------------------------------------
# 3. Smoke — detector off
# ---------------------------------------------------------------------------

class TestDetectorOff:
    def test_no_contrast_with_misconception_style(self) -> None:
        """Rule 1 (`contrast_with_misconception`) needs a DetectorHint.
        With the detector disabled, `_detector_hint_for` returns None and
        Rule 1 cannot fire — so no attempt carries that style.
        """
        runner, _ = _smoke_runner(
            detector_enabled=False,
            tutor_enabled=False,
            response_model="misconception_weighted",
        )
        attempts, _ = _drain_cohort(runner)
        assert len(attempts) > 0
        assert runner.misconception_detector is None
        styles = {a.explanation_style for a in attempts}
        assert "contrast_with_misconception" not in styles


# ---------------------------------------------------------------------------
# 4. Smoke — tutor off
# ---------------------------------------------------------------------------

class TestTutorOff:
    def test_no_llm_calls_and_no_explanations(self) -> None:
        runner, mock_client = _smoke_runner(
            detector_enabled=True,
            tutor_enabled=False,
            response_model="misconception_weighted",
        )
        assert mock_client is None
        assert runner.llm_tutor is None
        _, teaches = _drain_cohort(runner)
        assert len(teaches) > 0
        assert all(t.llm_explanation is None for t in teaches)

    def test_tutor_on_does_call_client(self) -> None:
        """Sanity check the inverse — tutor on → client is called."""
        runner, mock_client = _smoke_runner(
            detector_enabled=False,
            tutor_enabled=True,
            response_model="misconception_weighted",
        )
        assert mock_client is not None
        _, teaches = _drain_cohort(runner)
        assert len(teaches) > 0
        # Every teach with a style triggers one generate_explanation call.
        assert mock_client.messages.create.call_count >= 1
