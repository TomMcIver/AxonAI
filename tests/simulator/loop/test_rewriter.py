"""Tests for B8 QuestionRewriter."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.loop.rewriter import (
    QuestionRewriter,
    RewriteRecord,
    _parse_response,
    _synthetic_question,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client(reply: str) -> MagicMock:
    content_block = SimpleNamespace(text=reply)
    message = SimpleNamespace(content=[content_block])
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def _json_reply(question: str, distractors: list[str]) -> str:
    return json.dumps({"question": question, "distractors": distractors})


def _item(n_distractors: int = 2, *, b: float = 0.0) -> Item:
    return Item(
        item_id=10,
        concept_id=5,
        a=1.0,
        b=b,
        distractors=tuple(
            Distractor(option_text=f"wrong{i}", misconception_id=100 + i)
            for i in range(n_distractors)
        ),
    )


# ---------------------------------------------------------------------------
# _parse_response unit tests
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_valid_json_parsed(self):
        raw = json.dumps({"question": "What is 2+2?", "distractors": ["3", "5"]})
        q, ds = _parse_response(raw, n_distractors=2)
        assert q == "What is 2+2?"
        assert ds == ("3", "5")

    def test_strips_markdown_fences(self):
        raw = "```json\n" + json.dumps({"question": "Q?", "distractors": ["A"]}) + "\n```"
        q, ds = _parse_response(raw, n_distractors=1)
        assert q == "Q?"
        assert ds == ("A",)

    def test_too_few_distractors_falls_back(self):
        # Model returned 1 distractor but 2 are needed → fallback with warning.
        raw = json.dumps({"question": "Q?", "distractors": ["A"]})
        with pytest.warns(UserWarning, match="could not parse"):
            q, ds = _parse_response(raw, n_distractors=2)
        assert ds == ()

    def test_malformed_json_falls_back(self):
        with pytest.warns(UserWarning):
            q, ds = _parse_response("not json at all", n_distractors=1)
        assert ds == ()

    def test_extra_distractors_truncated(self):
        # Model returned 3 distractors but we only need 2 — truncated to 2.
        raw = json.dumps({"question": "Q?", "distractors": ["A", "B", "C"]})
        q, ds = _parse_response(raw, n_distractors=2)
        assert ds == ("A", "B")


# ---------------------------------------------------------------------------
# _synthetic_question unit tests
# ---------------------------------------------------------------------------

class TestSyntheticQuestion:
    def test_easy_label_for_low_b(self):
        item = _item(b=-1.0)
        q = _synthetic_question(item, concept_description=None)
        assert "easy" in q

    def test_hard_label_for_high_b(self):
        item = _item(b=1.5)
        q = _synthetic_question(item, concept_description=None)
        assert "hard" in q

    def test_moderate_label_for_middle_b(self):
        item = _item(b=0.0)
        q = _synthetic_question(item, None)
        assert "moderate" in q

    def test_concept_description_included(self):
        item = _item()
        q = _synthetic_question(item, "linear equations")
        assert "linear equations" in q

    def test_fallback_concept_id_when_no_description(self):
        item = _item()
        q = _synthetic_question(item, None)
        assert str(item.concept_id) in q


# ---------------------------------------------------------------------------
# QuestionRewriter.rewrite tests
# ---------------------------------------------------------------------------

class TestRewrite:
    def test_returns_rewritten_question_and_distractors(self):
        reply = _json_reply("Solve 3x = 12.", ["x = 3", "x = 36"])
        client = _mock_client(reply)
        rw = QuestionRewriter(client=client)
        q, ds = rw.rewrite("Solve 2x = 8.", ["x = 4", "x = 16"])
        assert q == "Solve 3x = 12."
        assert ds == ("x = 3", "x = 36")

    def test_calls_api_once(self):
        client = _mock_client(_json_reply("Q?", ["A", "B"]))
        rw = QuestionRewriter(client=client)
        rw.rewrite("original", ["d1", "d2"])
        assert client.messages.create.call_count == 1

    def test_model_forwarded(self):
        client = _mock_client(_json_reply("Q?", ["A"]))
        rw = QuestionRewriter(model="claude-haiku-4-5-20251001", client=client)
        rw.rewrite("q", ["d"])
        assert client.messages.create.call_args.kwargs["model"] == "claude-haiku-4-5-20251001"

    def test_max_tokens_forwarded(self):
        client = _mock_client(_json_reply("Q?", []))
        rw = QuestionRewriter(max_tokens=200, client=client)
        rw.rewrite("q", [])
        assert client.messages.create.call_args.kwargs["max_tokens"] == 200

    def test_concept_description_in_user_content(self):
        client = _mock_client(_json_reply("Q?", ["A"]))
        rw = QuestionRewriter(client=client)
        rw.rewrite("q", ["d"], concept_description="fractions")
        msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "fractions" in msg

    def test_api_error_returns_original_with_warning(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("timeout")
        rw = QuestionRewriter(client=client)
        with pytest.warns(UserWarning, match="rewrite failed"):
            q, ds = rw.rewrite("original q", ["d1", "d2"])
        assert q == "original q"
        assert ds == ("d1", "d2")

    def test_empty_distractors_roundtrip(self):
        reply = _json_reply("New Q?", [])
        client = _mock_client(reply)
        rw = QuestionRewriter(client=client)
        q, ds = rw.rewrite("old q", [])
        assert ds == ()


# ---------------------------------------------------------------------------
# QuestionRewriter.rewrite_item tests
# ---------------------------------------------------------------------------

class TestRewriteItem:
    def test_returns_rewrite_record(self):
        reply = _json_reply("New q?", ["new d0", "new d1"])
        client = _mock_client(reply)
        rw = QuestionRewriter(client=client)
        record = rw.rewrite_item(_item(n_distractors=2))
        assert isinstance(record, RewriteRecord)

    def test_is_simulated_always_true(self):
        client = _mock_client(_json_reply("Q?", ["d0", "d1"]))
        rw = QuestionRewriter(client=client)
        record = rw.rewrite_item(_item(n_distractors=2))
        assert record.is_simulated is True

    def test_original_item_id_preserved(self):
        client = _mock_client(_json_reply("Q?", ["d0"]))
        rw = QuestionRewriter(client=client)
        item = _item(n_distractors=1)
        record = rw.rewrite_item(item)
        assert record.original_item_id == item.item_id

    def test_explicit_question_text_used(self):
        client = _mock_client(_json_reply("rewritten", ["d0"]))
        rw = QuestionRewriter(client=client)
        rw.rewrite_item(_item(n_distractors=1), question_text="my question")
        msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "my question" in msg

    def test_synthetic_question_when_none(self):
        client = _mock_client(_json_reply("rewritten", ["d0", "d1"]))
        rw = QuestionRewriter(client=client)
        item = _item(n_distractors=2, b=1.5)
        record = rw.rewrite_item(item)
        assert "[Synthetic]" in record.original_question_text

    def test_original_distractors_recorded(self):
        client = _mock_client(_json_reply("Q?", ["x0", "x1"]))
        rw = QuestionRewriter(client=client)
        item = _item(n_distractors=2)
        record = rw.rewrite_item(item)
        assert record.original_distractor_texts == ("wrong0", "wrong1")

    def test_rewritten_distractors_recorded(self):
        client = _mock_client(_json_reply("Q?", ["x0", "x1"]))
        rw = QuestionRewriter(client=client)
        record = rw.rewrite_item(_item(n_distractors=2))
        assert record.rewritten_distractor_texts == ("x0", "x1")


# ---------------------------------------------------------------------------
# RewriteRecord.to_item_variant tests
# ---------------------------------------------------------------------------

class TestToItemVariant:
    def test_produces_item_with_new_id(self):
        item = _item(n_distractors=2)
        record = RewriteRecord(
            original_item_id=item.item_id,
            concept_id=item.concept_id,
            original_question_text="orig",
            rewritten_question_text="rewritten",
            original_distractor_texts=("wrong0", "wrong1"),
            rewritten_distractor_texts=("new0", "new1"),
        )
        variant = record.to_item_variant(new_item_id=999, original_item=item)
        assert variant.item_id == 999

    def test_irt_params_preserved(self):
        item = Item(item_id=1, concept_id=3, a=1.5, b=-0.3)
        record = RewriteRecord(
            original_item_id=1, concept_id=3,
            original_question_text="o", rewritten_question_text="r",
            original_distractor_texts=(), rewritten_distractor_texts=(),
        )
        variant = record.to_item_variant(new_item_id=2, original_item=item)
        assert variant.a == pytest.approx(1.5)
        assert variant.b == pytest.approx(-0.3)

    def test_misconception_ids_carried_over(self):
        item = _item(n_distractors=2)  # misconception_ids 100, 101
        record = RewriteRecord(
            original_item_id=item.item_id, concept_id=item.concept_id,
            original_question_text="o", rewritten_question_text="r",
            original_distractor_texts=("wrong0", "wrong1"),
            rewritten_distractor_texts=("new0", "new1"),
        )
        variant = record.to_item_variant(new_item_id=50, original_item=item)
        assert variant.distractors[0].misconception_id == 100
        assert variant.distractors[1].misconception_id == 101

    def test_rewritten_option_texts_used(self):
        item = _item(n_distractors=1)
        record = RewriteRecord(
            original_item_id=item.item_id, concept_id=item.concept_id,
            original_question_text="o", rewritten_question_text="r",
            original_distractor_texts=("wrong0",),
            rewritten_distractor_texts=("new option",),
        )
        variant = record.to_item_variant(new_item_id=77, original_item=item)
        assert variant.distractors[0].option_text == "new option"

    def test_concept_id_preserved(self):
        item = _item()
        record = RewriteRecord(
            original_item_id=item.item_id, concept_id=item.concept_id,
            original_question_text="o", rewritten_question_text="r",
            original_distractor_texts=(), rewritten_distractor_texts=(),
        )
        variant = record.to_item_variant(new_item_id=5, original_item=item)
        assert variant.concept_id == item.concept_id
