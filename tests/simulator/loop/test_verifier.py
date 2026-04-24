"""Tests for B9 RewriteVerifier."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ml.simulator.loop.rewriter import RewriteRecord
from ml.simulator.loop.verifier import (
    RewriteVerifier,
    VerificationResult,
    _parse_verification,
    verify_batch,
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


def _json_reply(equivalent: bool, confidence: float, reason: str = "Same concept.") -> str:
    return json.dumps({"equivalent": equivalent, "confidence": confidence, "reason": reason})


def _record(
    item_id: int = 10,
    concept_id: int = 5,
    orig: str = "Solve 2x = 8.",
    rewritten: str = "Solve 3x = 12.",
) -> RewriteRecord:
    return RewriteRecord(
        original_item_id=item_id,
        concept_id=concept_id,
        original_question_text=orig,
        rewritten_question_text=rewritten,
        original_distractor_texts=("x=2",),
        rewritten_distractor_texts=("x=3",),
    )


# ---------------------------------------------------------------------------
# _parse_verification unit tests
# ---------------------------------------------------------------------------

class TestParseVerification:
    def test_valid_json_parsed(self):
        raw = _json_reply(True, 0.95, "Both solve a one-step equation.")
        result = _parse_verification(raw)
        assert result["equivalent"] is True
        assert result["confidence"] == pytest.approx(0.95)
        assert "one-step" in result["reason"]

    def test_strips_markdown_fences(self):
        raw = "```json\n" + _json_reply(False, 0.3) + "\n```"
        result = _parse_verification(raw)
        assert result["equivalent"] is False

    def test_confidence_clamped_to_0_1(self):
        raw = json.dumps({"equivalent": True, "confidence": 1.5, "reason": "ok"})
        result = _parse_verification(raw)
        assert result["confidence"] == pytest.approx(1.0)

        raw2 = json.dumps({"equivalent": False, "confidence": -0.5, "reason": "ok"})
        result2 = _parse_verification(raw2)
        assert result2["confidence"] == pytest.approx(0.0)

    def test_malformed_json_defaults_with_warning(self):
        with pytest.warns(UserWarning, match="could not parse"):
            result = _parse_verification("not valid json")
        assert result["equivalent"] is False
        assert result["confidence"] == pytest.approx(0.0)

    def test_missing_fields_use_defaults(self):
        raw = json.dumps({})  # all fields missing
        result = _parse_verification(raw)
        assert result["equivalent"] is False
        assert result["confidence"] == pytest.approx(0.0)
        assert result["reason"] == ""


# ---------------------------------------------------------------------------
# RewriteVerifier.verify unit tests
# ---------------------------------------------------------------------------

class TestVerify:
    def test_returns_verification_result(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert isinstance(result, VerificationResult)

    def test_equivalent_true_propagated(self):
        client = _mock_client(_json_reply(True, 0.88, "Same linear equation type."))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert result.is_equivalent is True

    def test_equivalent_false_propagated(self):
        client = _mock_client(_json_reply(False, 0.72, "Different concept."))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert result.is_equivalent is False

    def test_confidence_propagated(self):
        client = _mock_client(_json_reply(True, 0.76))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert result.confidence == pytest.approx(0.76)

    def test_reason_propagated(self):
        client = _mock_client(_json_reply(True, 0.9, "Both test division."))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert "division" in result.reason

    def test_is_simulated_always_true(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(client=client)
        result = v.verify(_record())
        assert result.is_simulated is True

    def test_original_item_id_preserved(self):
        client = _mock_client(_json_reply(True, 0.85))
        v = RewriteVerifier(client=client)
        r = _record(item_id=42)
        result = v.verify(r)
        assert result.original_item_id == 42

    def test_concept_id_preserved(self):
        client = _mock_client(_json_reply(True, 0.85))
        v = RewriteVerifier(client=client)
        r = _record(concept_id=7)
        result = v.verify(r)
        assert result.concept_id == 7

    def test_original_and_rewritten_in_user_prompt(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(client=client)
        r = _record(orig="Solve 2x = 8.", rewritten="Solve 3y = 15.")
        v.verify(r)
        msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "Solve 2x = 8." in msg
        assert "Solve 3y = 15." in msg

    def test_api_error_defaults_to_non_equivalent_with_warning(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("network error")
        v = RewriteVerifier(client=client)
        with pytest.warns(UserWarning, match="verify failed"):
            result = v.verify(_record())
        assert result.is_equivalent is False
        assert result.confidence == pytest.approx(0.0)

    def test_model_forwarded(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(model="claude-haiku-4-5-20251001", client=client)
        v.verify(_record())
        assert client.messages.create.call_args.kwargs["model"] == "claude-haiku-4-5-20251001"

    def test_max_tokens_forwarded(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(max_tokens=60, client=client)
        v.verify(_record())
        assert client.messages.create.call_args.kwargs["max_tokens"] == 60


# ---------------------------------------------------------------------------
# verify_batch tests
# ---------------------------------------------------------------------------

class TestVerifyBatch:
    def _make_verifier(self, confidence: float) -> RewriteVerifier:
        client = _mock_client(_json_reply(True, confidence))
        return RewriteVerifier(client=client)

    def test_returns_list_of_results(self):
        v = self._make_verifier(0.9)
        records = [_record(item_id=i) for i in range(3)]
        results = verify_batch(v, records)
        assert isinstance(results, list)
        assert all(isinstance(r, VerificationResult) for r in results)

    def test_high_confidence_kept(self):
        v = self._make_verifier(0.85)
        results = verify_batch(v, [_record()], confidence_threshold=0.7)
        assert len(results) == 1

    def test_low_confidence_filtered(self):
        v = self._make_verifier(0.5)
        results = verify_batch(v, [_record()], confidence_threshold=0.7)
        assert len(results) == 0

    def test_empty_input_returns_empty(self):
        v = self._make_verifier(0.9)
        assert verify_batch(v, []) == []

    def test_calls_verify_once_per_record(self):
        client = _mock_client(_json_reply(True, 0.9))
        v = RewriteVerifier(client=client)
        records = [_record(item_id=i) for i in range(4)]
        verify_batch(v, records)
        assert client.messages.create.call_count == 4

    def test_default_threshold_is_applied(self):
        # Default threshold is 0.7 — confidence=0.65 should be filtered.
        client = _mock_client(_json_reply(True, 0.65))
        v = RewriteVerifier(client=client)
        results = verify_batch(v, [_record()])
        assert len(results) == 0
