"""Tests for B7 LLMTutor and teach-step integration."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ml.simulator.loop.explanation_style import (
    ANALOGY,
    CONCISE_ANSWER,
    CONTRAST_WITH_MISCONCEPTION,
    HINT,
    WORKED_EXAMPLE,
)
from ml.simulator.loop.llm_tutor import LLMTutor, _STYLE_INSTRUCTIONS
from ml.simulator.loop.teach import TeachRecord, teach
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client(reply: str = "Here is the explanation.") -> MagicMock:
    """Build a minimal anthropic-shaped mock that returns `reply`."""
    content_block = SimpleNamespace(text=reply)
    message = SimpleNamespace(content=[content_block])
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def _profile() -> StudentProfile:
    return StudentProfile(
        student_id=1,
        true_theta={1: 0.0},
        estimated_theta={1: (0.0, 1.0)},
        bkt_state={1: BKTState(p_known=0.3)},
        elo_rating=1200.0,
        recall_half_life={1: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
    )


# ---------------------------------------------------------------------------
# LLMTutor unit tests
# ---------------------------------------------------------------------------

class TestLLMTutorGenerate:
    def test_returns_string_from_client(self):
        client = _mock_client("Fractions represent parts of a whole.")
        tutor = LLMTutor(client=client)
        result = tutor.generate_explanation(concept_id=3, explanation_style=CONCISE_ANSWER)
        assert result == "Fractions represent parts of a whole."

    def test_calls_messages_create_once(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(concept_id=5, explanation_style=WORKED_EXAMPLE)
        assert client.messages.create.call_count == 1

    def test_model_forwarded(self):
        client = _mock_client()
        tutor = LLMTutor(model="claude-haiku-4-5-20251001", client=client)
        tutor.generate_explanation(concept_id=1, explanation_style=CONCISE_ANSWER)
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

    def test_max_tokens_forwarded(self):
        client = _mock_client()
        tutor = LLMTutor(max_tokens=80, client=client)
        tutor.generate_explanation(concept_id=1, explanation_style=HINT)
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 80

    def test_concept_description_in_user_content(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(
            concept_id=7, explanation_style=ANALOGY,
            concept_description="quadratic equations"
        )
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "quadratic equations" in user_msg

    def test_fallback_description_when_none(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(concept_id=99, explanation_style=CONCISE_ANSWER)
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "99" in user_msg

    def test_misconception_id_appended_for_contrast_style(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(
            concept_id=1, explanation_style=CONTRAST_WITH_MISCONCEPTION,
            misconception_id=42,
        )
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "42" in user_msg

    def test_misconception_id_not_appended_for_other_styles(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(
            concept_id=1, explanation_style=WORKED_EXAMPLE,
            misconception_id=42,
        )
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        # misconception ID should not be mentioned for non-contrast styles
        assert "42" not in user_msg

    def test_api_error_returns_empty_string_with_warning(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("network error")
        tutor = LLMTutor(client=client)
        with pytest.warns(UserWarning, match="LLMTutor failed"):
            result = tutor.generate_explanation(concept_id=1, explanation_style=CONCISE_ANSWER)
        assert result == ""

    @pytest.mark.parametrize("style", [
        CONTRAST_WITH_MISCONCEPTION, WORKED_EXAMPLE, HINT, ANALOGY, CONCISE_ANSWER,
    ])
    def test_all_styles_produce_distinct_instructions(self, style):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        tutor.generate_explanation(concept_id=1, explanation_style=style)
        user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert _STYLE_INSTRUCTIONS[style] in user_msg


# ---------------------------------------------------------------------------
# teach() integration with LLMTutor
# ---------------------------------------------------------------------------

class TestTeachWithTutor:
    def test_llm_explanation_stored_in_record(self):
        client = _mock_client("A helpful explanation.")
        tutor = LLMTutor(client=client)
        _, record = teach(
            _profile(), concept_id=1, now=datetime(2024, 1, 1),
            explanation_style=WORKED_EXAMPLE,
            llm_tutor=tutor,
        )
        assert record.llm_explanation == "A helpful explanation."
        assert record.explanation_style == WORKED_EXAMPLE

    def test_no_tutor_leaves_explanation_none(self):
        _, record = teach(
            _profile(), concept_id=1, now=datetime(2024, 1, 1),
            explanation_style=CONCISE_ANSWER,
            llm_tutor=None,
        )
        assert record.llm_explanation is None

    def test_no_style_skips_tutor_even_when_set(self):
        client = _mock_client()
        tutor = LLMTutor(client=client)
        _, record = teach(
            _profile(), concept_id=1, now=datetime(2024, 1, 1),
            explanation_style=None,
            llm_tutor=tutor,
        )
        client.messages.create.assert_not_called()
        assert record.llm_explanation is None

    def test_empty_string_from_api_stored_as_none(self):
        client = _mock_client("")  # API returned empty
        tutor = LLMTutor(client=client)
        _, record = teach(
            _profile(), concept_id=1, now=datetime(2024, 1, 1),
            explanation_style=HINT,
            llm_tutor=tutor,
        )
        assert record.llm_explanation is None

    def test_backward_compat_no_extra_args(self):
        # Old callers pass only (profile, concept_id, now); must still work.
        p = _profile()
        new_p, record = teach(p, concept_id=1, now=datetime(2024, 1, 1))
        assert record.explanation_style is None
        assert record.llm_explanation is None
        assert new_p.last_retrieval[1] == datetime(2024, 1, 1)


# ---------------------------------------------------------------------------
# TermRunner integration
# ---------------------------------------------------------------------------

class TestRunnerWithTutor:
    def test_runner_accepts_llm_tutor_field(self):
        import math
        import networkx as nx
        from ml.simulator.data.concept_graph import ConceptGraph
        from ml.simulator.data.item_bank import Item, ItemBank
        from ml.simulator.loop.runner import TermRunner
        from ml.simulator.psychometrics.bkt import BKTParams, BKTState

        g = nx.DiGraph()
        g.add_edge(1, 2)
        concept_graph = ConceptGraph(g)
        item = Item(item_id=1, concept_id=1, a=1.0, b=0.0)
        bank = ItemBank([item])
        bkt = {1: BKTParams(0.2, 0.1, 0.08, 0.2), 2: BKTParams(0.2, 0.1, 0.08, 0.2)}

        profile = StudentProfile(
            student_id=0,
            true_theta={1: 0.0, 2: 0.0},
            estimated_theta={1: (0.0, 1.0), 2: (0.0, 1.0)},
            bkt_state={c: BKTState(p_known=0.2) for c in (1, 2)},
            elo_rating=1200.0,
            recall_half_life={1: 24.0, 2: 24.0},
            last_retrieval={},
            learning_rate=0.1,
            slip=0.1,
            guess=0.25,
            engagement_decay=0.95,
            response_time_lognorm_params=(math.log(8000), 0.3),
        )

        client = _mock_client("Example explanation text.")
        tutor = LLMTutor(client=client)
        runner = TermRunner(
            student=profile,
            concept_graph=concept_graph,
            item_bank=bank,
            bkt_params_by_concept=bkt,
            start_time=datetime(2024, 1, 1),
            n_sessions=1,
            seed=0,
            llm_tutor=tutor,
        )
        events = list(runner.run())
        teach_events = [e for e in events if isinstance(e, TeachRecord)]
        assert teach_events
        tr = teach_events[0]
        assert tr.llm_explanation == "Example explanation text."
        assert tr.explanation_style is not None
        # LLM was called exactly once (one teach event)
        assert client.messages.create.call_count == 1
