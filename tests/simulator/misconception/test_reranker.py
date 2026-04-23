"""Tests for the B4 cross-encoder reranker.

Uses a mock CrossEncoder that scores by name length (deterministic).
No network download required.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from ml.simulator.misconception.reranker import (
    evaluate_rerank,
    rerank,
    top_prediction,
)
from ml.simulator.misconception.retrieval import MisconceptionEntry


def _fake_ce_model(score_fn=None):
    """CrossEncoder mock. Default: scores = negative string length of candidate."""
    def default_score(pairs, **kwargs):
        return np.array([-len(c) for _, c in pairs], dtype=np.float32)

    fn = score_fn or default_score
    m = MagicMock()
    m.predict.side_effect = fn
    return m


def _candidates(*names: str) -> list[tuple[MisconceptionEntry, float]]:
    return [
        (MisconceptionEntry(misconception_id=i, name=n), float(i))
        for i, n in enumerate(names)
    ]


class TestRerank:
    def test_returns_same_length(self):
        cands = _candidates("short", "medium length", "a very long name indeed")
        model = _fake_ce_model()
        result = rerank("query", cands, model=model)
        assert len(result) == len(cands)

    def test_sorted_descending_by_ce_score(self):
        cands = _candidates("a", "bb", "ccc")
        # Score fn: -len → shortest = highest score.
        model = _fake_ce_model()
        result = rerank("query", cands, model=model)
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_candidates_returns_empty(self):
        model = _fake_ce_model()
        assert rerank("q", [], model=model) == []

    def test_returns_misconception_entry_and_float_pairs(self):
        cands = _candidates("A", "B")
        model = _fake_ce_model()
        result = rerank("q", cands, model=model)
        for entry, score in result:
            assert isinstance(entry, MisconceptionEntry)
            assert isinstance(score, float)

    def test_single_candidate_returned(self):
        cands = _candidates("only")
        model = _fake_ce_model()
        result = rerank("q", cands, model=model)
        assert len(result) == 1

    def test_uses_entry_name_in_pair(self):
        """The CE model receives (query, entry.name) pairs."""
        seen_pairs = []

        def capture_fn(pairs, **kwargs):
            seen_pairs.extend(pairs)
            return np.zeros(len(pairs), dtype=np.float32)

        model = _fake_ce_model(capture_fn)
        cands = _candidates("my_name")
        rerank("test_query", cands, model=model)
        assert any("my_name" in c for _, c in seen_pairs)
        assert any("test_query" == q for q, _ in seen_pairs)

    def test_nameless_entry_gets_fallback_text(self):
        """Entry with empty name → 'Misconception {id}' in the pair."""
        cands = [(MisconceptionEntry(misconception_id=7, name=""), 0.5)]
        seen = []

        def capture(pairs, **kwargs):
            seen.extend(pairs)
            return np.zeros(len(pairs), dtype=np.float32)

        model = _fake_ce_model(capture)
        rerank("q", cands, model=model)
        assert any("Misconception 7" in c for _, c in seen)


class TestTopPrediction:
    def test_returns_top_entry(self):
        entry = MisconceptionEntry(1, "M1")
        reranked = [(entry, 0.9), (MisconceptionEntry(2, "M2"), 0.3)]
        result_entry, score = top_prediction(reranked)
        assert result_entry is entry
        assert score == pytest.approx(0.9)

    def test_empty_returns_none(self):
        e, s = top_prediction([])
        assert e is None
        assert s == 0.0

    def test_below_threshold_returns_none(self):
        reranked = [(MisconceptionEntry(1, "M"), 0.2)]
        e, s = top_prediction(reranked, confidence_threshold=0.5)
        assert e is None
        assert s == pytest.approx(0.2)

    def test_above_threshold_returns_entry(self):
        entry = MisconceptionEntry(1, "M")
        reranked = [(entry, 0.8)]
        e, s = top_prediction(reranked, confidence_threshold=0.5)
        assert e is entry

    def test_default_threshold_accepts_negative_logits(self):
        """CE logits can be negative; default -inf threshold must accept them."""
        entry = MisconceptionEntry(1, "M")
        reranked = [(entry, -5.0)]
        e, _ = top_prediction(reranked)
        assert e is entry


class TestEvaluateRerank:
    def test_perfect_p1_and_mrr(self):
        e = MisconceptionEntry(42, "M42")
        results = [(42, [(e, 0.9), (MisconceptionEntry(1, "M1"), 0.1)])]
        m = evaluate_rerank(results)
        assert m["precision_at_1"] == pytest.approx(1.0)
        assert m["mrr"] == pytest.approx(1.0)

    def test_miss_gives_zero_p1_mrr(self):
        results = [(99, [(MisconceptionEntry(1, "M1"), 0.9)])]
        m = evaluate_rerank(results)
        assert m["precision_at_1"] == pytest.approx(0.0)
        assert m["mrr"] == pytest.approx(0.0)

    def test_rank_2_gives_mrr_half(self):
        e99 = MisconceptionEntry(99, "M99")
        e1 = MisconceptionEntry(1, "M1")
        results = [(99, [(e1, 0.9), (e99, 0.5)])]
        m = evaluate_rerank(results)
        assert m["mrr"] == pytest.approx(0.5)

    def test_empty_returns_zeros(self):
        m = evaluate_rerank([])
        assert m["precision_at_1"] == 0.0
        assert m["mrr"] == 0.0
        assert m["n_queries"] == 0

    def test_n_queries_matches_input(self):
        entry = MisconceptionEntry(1, "M1")
        results = [(1, [(entry, 0.9)]) for _ in range(7)]
        m = evaluate_rerank(results)
        assert m["n_queries"] == 7
