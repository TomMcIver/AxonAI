"""Tests for B10 rewriter sample-testing harness."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ml.simulator.data.item_bank import Distractor, Item, ItemBank
from ml.simulator.loop.rewriter import QuestionRewriter, RewriteRecord
from ml.simulator.loop.verifier import RewriteVerifier, VerificationResult
from ml.simulator.validation.rewriter_harness import (
    HarnessReport,
    ItemHarnessRecord,
    _confidence_histogram,
    run_harness,
    sample_items,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(item_id: int, concept_id: int = 1, b: float = 0.0) -> Item:
    return Item(
        item_id=item_id, concept_id=concept_id, a=1.0, b=b,
        distractors=(Distractor(option_text=f"wrong{item_id}"),),
    )


def _bank(n: int = 5) -> ItemBank:
    return ItemBank([_item(i) for i in range(1, n + 1)])


def _mock_rewriter(question: str = "Rewritten Q", distractor: str = "rw") -> QuestionRewriter:
    """Rewriter whose API returns a fixed rewritten question."""
    reply = json.dumps({"question": question, "distractors": [distractor]})
    content = SimpleNamespace(text=reply)
    msg = SimpleNamespace(content=[content])
    client = MagicMock()
    client.messages.create.return_value = msg
    return QuestionRewriter(client=client)


def _mock_verifier(
    equivalent: bool = True,
    confidence: float = 0.85,
    reason: str = "Same concept.",
) -> RewriteVerifier:
    """Verifier whose API returns fixed equivalence result."""
    reply = json.dumps({"equivalent": equivalent, "confidence": confidence, "reason": reason})
    content = SimpleNamespace(text=reply)
    msg = SimpleNamespace(content=[content])
    client = MagicMock()
    client.messages.create.return_value = msg
    return RewriteVerifier(client=client)


# ---------------------------------------------------------------------------
# sample_items tests
# ---------------------------------------------------------------------------

class TestSampleItems:
    def test_returns_list_of_items(self):
        bank = _bank(5)
        result = sample_items(bank, n_samples=3)
        assert isinstance(result, list)
        assert all(isinstance(i, Item) for i in result)

    def test_n_samples_respected(self):
        bank = _bank(10)
        result = sample_items(bank, n_samples=4)
        assert len(result) == 4

    def test_no_duplicates(self):
        bank = _bank(8)
        result = sample_items(bank, n_samples=8)
        ids = [i.item_id for i in result]
        assert len(set(ids)) == 8

    def test_none_samples_returns_all(self):
        bank = _bank(6)
        result = sample_items(bank, n_samples=None)
        assert len(result) == 6

    def test_n_samples_exceeding_bank_returns_all(self):
        bank = _bank(4)
        result = sample_items(bank, n_samples=100)
        assert len(result) == 4

    def test_deterministic_with_same_seed(self):
        bank = _bank(10)
        r1 = sample_items(bank, n_samples=5, seed=7)
        r2 = sample_items(bank, n_samples=5, seed=7)
        assert [i.item_id for i in r1] == [i.item_id for i in r2]

    def test_different_seeds_produce_different_order(self):
        bank = _bank(10)
        r1 = sample_items(bank, n_samples=10, seed=1)
        r2 = sample_items(bank, n_samples=10, seed=2)
        # Very unlikely to be identical for 10 items
        assert [i.item_id for i in r1] != [i.item_id for i in r2]

    def test_empty_bank_returns_empty(self):
        bank = ItemBank([])
        result = sample_items(bank, n_samples=5)
        assert result == []


# ---------------------------------------------------------------------------
# _confidence_histogram tests
# ---------------------------------------------------------------------------

class TestConfidenceHistogram:
    def test_length_equals_n_bins(self):
        hist = _confidence_histogram([0.5, 0.9], n_bins=5)
        assert len(hist) == 5

    def test_sum_equals_n_values(self):
        values = [0.1, 0.3, 0.7, 0.95]
        hist = _confidence_histogram(values, n_bins=5)
        assert sum(hist) == 4

    def test_perfect_confidence_in_last_bin(self):
        hist = _confidence_histogram([1.0], n_bins=5)
        assert hist[-1] == 1

    def test_zero_confidence_in_first_bin(self):
        hist = _confidence_histogram([0.0], n_bins=5)
        assert hist[0] == 1

    def test_empty_input_all_zeros(self):
        hist = _confidence_histogram([], n_bins=4)
        assert hist == (0, 0, 0, 0)


# ---------------------------------------------------------------------------
# run_harness tests
# ---------------------------------------------------------------------------

class TestRunHarness:
    def test_returns_harness_report(self):
        rw = _mock_rewriter()
        v = _mock_verifier()
        report = run_harness([_item(1)], rw, v)
        assert isinstance(report, HarnessReport)

    def test_n_sampled_matches_input(self):
        rw = _mock_rewriter()
        v = _mock_verifier()
        items = [_item(i) for i in range(1, 6)]
        report = run_harness(items, rw, v)
        assert report.n_sampled == 5

    def test_equivalent_counted(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=True, confidence=0.9)
        report = run_harness([_item(1)], rw, v, confidence_threshold=0.7)
        assert report.n_equivalent == 1
        assert report.n_non_equivalent == 0

    def test_non_equivalent_counted(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=False, confidence=0.9)
        report = run_harness([_item(1)], rw, v, confidence_threshold=0.7)
        assert report.n_equivalent == 0
        assert report.n_non_equivalent == 1

    def test_low_confidence_counted_separately(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=True, confidence=0.4)
        report = run_harness([_item(1)], rw, v, confidence_threshold=0.7)
        assert report.n_low_confidence == 1
        assert report.n_equivalent == 0

    def test_pass_rate_all_equivalent(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=True, confidence=0.9)
        items = [_item(i) for i in range(1, 5)]
        report = run_harness(items, rw, v, confidence_threshold=0.7)
        assert report.pass_rate == pytest.approx(1.0)

    def test_pass_rate_partial(self):
        # 2 equivalent (high conf), 1 non-equivalent (high conf), 1 low-conf
        # pass_rate = n_equivalent / n_sampled = 2 / 4 = 0.5
        results = [
            (True, 0.9), (True, 0.9), (False, 0.9), (True, 0.3),
        ]
        call_count = [0]

        def make_reply(eq, conf):
            return json.dumps({"equivalent": eq, "confidence": conf, "reason": "ok"})

        # Use side_effect to return different values per call
        content_blocks = [SimpleNamespace(text=make_reply(eq, conf)) for eq, conf in results]
        messages = [SimpleNamespace(content=[cb]) for cb in content_blocks]
        client_rw = MagicMock()
        client_rw.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(text=json.dumps({"question": "Q?", "distractors": ["d"]}))]
        )
        rw = QuestionRewriter(client=client_rw)

        client_v = MagicMock()
        client_v.messages.create.side_effect = messages
        v = RewriteVerifier(client=client_v)

        items = [_item(i) for i in range(1, 5)]
        report = run_harness(items, rw, v, confidence_threshold=0.7)
        assert report.pass_rate == pytest.approx(0.5)  # 2/4

    def test_passed_flag_true_above_threshold(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=True, confidence=0.9)
        items = [_item(i) for i in range(1, 9)]
        report = run_harness(items, rw, v, acceptance_threshold=0.8)
        assert report.passed is True

    def test_passed_flag_false_below_threshold(self):
        rw = _mock_rewriter()
        v = _mock_verifier(equivalent=False, confidence=0.9)
        report = run_harness([_item(1)], rw, v, acceptance_threshold=0.8)
        assert report.passed is False

    def test_empty_items_returns_zero_report(self):
        rw = _mock_rewriter()
        v = _mock_verifier()
        report = run_harness([], rw, v)
        assert report.n_sampled == 0
        assert report.pass_rate == pytest.approx(0.0)
        assert report.passed is False

    def test_records_length_matches_items(self):
        rw = _mock_rewriter()
        v = _mock_verifier()
        items = [_item(i) for i in range(1, 4)]
        report = run_harness(items, rw, v)
        assert len(report.records) == 3

    def test_records_are_item_harness_record(self):
        rw = _mock_rewriter()
        v = _mock_verifier()
        report = run_harness([_item(1)], rw, v)
        assert isinstance(report.records[0], ItemHarnessRecord)

    def test_concept_description_map_forwarded(self):
        client_rw = MagicMock()
        client_rw.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(
                text=json.dumps({"question": "Q?", "distractors": ["d"]})
            )]
        )
        rw = QuestionRewriter(client=client_rw)
        v = _mock_verifier()

        item = Item(item_id=1, concept_id=7, a=1.0, b=0.0,
                    distractors=(Distractor(option_text="wrong"),))
        cdm = {7: "linear equations"}
        run_harness([item], rw, v, concept_description_map=cdm)
        msg = client_rw.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "linear equations" in msg

    def test_histogram_length_correct(self):
        rw = _mock_rewriter()
        v = _mock_verifier(confidence=0.85)
        items = [_item(i) for i in range(1, 4)]
        report = run_harness(items, rw, v)
        assert len(report.confidence_histogram) == 5  # _HISTOGRAM_N_BINS

    def test_mean_confidence_correct(self):
        rw = _mock_rewriter()
        v = _mock_verifier(confidence=0.8)
        items = [_item(i) for i in range(1, 4)]
        report = run_harness(items, rw, v)
        assert report.mean_confidence == pytest.approx(0.8)
