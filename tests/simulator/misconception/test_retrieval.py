"""Tests for the B3 misconception retrieval module.

Tests use a fake embedding model (returns random-but-seeded vectors) so
no network download is needed and the suite stays fast. The real
`sentence-transformers` model is exercised by the eval script.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from ml.simulator.misconception.retrieval import (
    DEFAULT_TOP_K,
    MisconceptionEntry,
    MisconceptionIndex,
    RetrievalEvalRow,
    build_index,
    build_query_text,
    build_train_test_split,
    evaluate_retrieval,
    recall_at_k,
    retrieve,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_model(n_dim: int = 32, seed: int = 0) -> MagicMock:
    """Returns a mock SentenceTransformer that produces L2-normalised vecs."""
    rng = np.random.default_rng(seed)

    def encode(texts, **kwargs):
        vecs = rng.standard_normal((len(texts), n_dim)).astype(np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.maximum(norms, 1e-8)

    m = MagicMock()
    m.encode.side_effect = encode
    return m


def _catalogue(n: int) -> list[MisconceptionEntry]:
    return [
        MisconceptionEntry(misconception_id=i, name=f"Misconception {i}")
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# MisconceptionEntry
# ---------------------------------------------------------------------------


class TestMisconceptionEntry:
    def test_stores_id_and_name(self):
        e = MisconceptionEntry(misconception_id=42, name="Confuses plus and minus")
        assert e.misconception_id == 42
        assert e.name == "Confuses plus and minus"

    def test_empty_name_allowed(self):
        e = MisconceptionEntry(misconception_id=0, name="")
        assert e.name == ""


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------


class TestBuildIndex:
    def test_output_shape(self):
        cat = _catalogue(10)
        model = _fake_model()
        idx = build_index(cat, model=model)
        assert idx.embeddings.shape[0] == 10
        assert idx.embeddings.dtype == np.float32

    def test_entries_order_preserved(self):
        cat = _catalogue(5)
        model = _fake_model()
        idx = build_index(cat, model=model)
        assert [e.misconception_id for e in idx.entries] == [0, 1, 2, 3, 4]

    def test_embeddings_are_normalised(self):
        cat = _catalogue(5)
        idx = build_index(cat, model=_fake_model())
        norms = np.linalg.norm(idx.embeddings, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# retrieve
# ---------------------------------------------------------------------------


class TestRetrieve:
    def test_returns_top_k_results(self):
        cat = _catalogue(50)
        model = _fake_model()
        idx = build_index(cat, model=model)
        hits = retrieve(idx, "some query", top_k=10, model=model)
        assert len(hits) == 10

    def test_results_sorted_descending_by_score(self):
        cat = _catalogue(50)
        model = _fake_model()
        idx = build_index(cat, model=model)
        hits = retrieve(idx, "some query", top_k=10, model=model)
        scores = [s for _, s in hits]
        assert scores == sorted(scores, reverse=True)

    def test_returns_tuples_of_entry_and_float(self):
        cat = _catalogue(5)
        model = _fake_model()
        idx = build_index(cat, model=model)
        hits = retrieve(idx, "q", top_k=3, model=model)
        for entry, score in hits:
            assert isinstance(entry, MisconceptionEntry)
            assert isinstance(score, float)

    def test_top_k_capped_at_catalogue_size(self):
        cat = _catalogue(3)
        model = _fake_model()
        idx = build_index(cat, model=model)
        hits = retrieve(idx, "q", top_k=100, model=model)
        assert len(hits) == 3

    def test_scores_in_valid_cosine_range(self):
        cat = _catalogue(20)
        model = _fake_model()
        idx = build_index(cat, model=model)
        hits = retrieve(idx, "q", top_k=5, model=model)
        for _, s in hits:
            assert -1.0 <= s <= 1.0 + 1e-5


# ---------------------------------------------------------------------------
# build_query_text
# ---------------------------------------------------------------------------


class TestBuildQueryText:
    def test_contains_sep_token(self):
        q = build_query_text("What is 2+2?", "5")
        assert "[SEP]" in q

    def test_strips_whitespace(self):
        q = build_query_text("  q  ", "  a  ")
        assert not q.startswith(" ")


# ---------------------------------------------------------------------------
# build_train_test_split
# ---------------------------------------------------------------------------


class TestBuildTrainTestSplit:
    def test_sizes_sum_to_total(self):
        cat = _catalogue(100)
        train, test = build_train_test_split(cat)
        assert len(train) + len(test) == 100

    def test_test_fraction_near_20_pct(self):
        cat = _catalogue(100)
        _, test = build_train_test_split(cat)
        assert 15 <= len(test) <= 25

    def test_ids_are_disjoint(self):
        cat = _catalogue(100)
        train, test = build_train_test_split(cat)
        train_ids = {e.misconception_id for e in train}
        test_ids = {e.misconception_id for e in test}
        assert train_ids & test_ids == set()

    def test_covers_full_catalogue(self):
        cat = _catalogue(100)
        train, test = build_train_test_split(cat)
        all_ids = {e.misconception_id for e in train + test}
        assert all_ids == {e.misconception_id for e in cat}

    def test_deterministic_under_seed(self):
        cat = _catalogue(100)
        t1, te1 = build_train_test_split(cat, seed=7)
        t2, te2 = build_train_test_split(cat, seed=7)
        assert [e.misconception_id for e in t1] == [e.misconception_id for e in t2]

    def test_different_seed_different_split(self):
        cat = _catalogue(100)
        _, te1 = build_train_test_split(cat, seed=1)
        _, te2 = build_train_test_split(cat, seed=2)
        assert [e.misconception_id for e in te1] != [e.misconception_id for e in te2]


# ---------------------------------------------------------------------------
# evaluate_retrieval + recall_at_k
# ---------------------------------------------------------------------------


class TestEvaluateRetrieval:
    def _build_deterministic_index(self, n=20):
        """Build an index where entry i has embedding = e_i (one-hot)."""
        entries = [MisconceptionEntry(i, f"M{i}") for i in range(n)]
        embeddings = np.eye(n, dtype=np.float32)
        return MisconceptionIndex(
            entries=entries,
            embeddings=embeddings,
            model_name="test",
            model_revision="test",
        ), entries

    def _one_hot_model(self, n=20):
        """Mock that returns the one-hot vector matching the first word 'M{i}'."""
        def encode(texts, **kwargs):
            out = []
            for t in texts:
                # pull out a number from "M{i}" anywhere in t
                import re
                m = re.search(r"\bM(\d+)\b", t)
                idx = int(m.group(1)) if m else 0
                vec = np.zeros(n, dtype=np.float32)
                vec[idx % n] = 1.0
                out.append(vec)
            return np.array(out)

        mock = MagicMock()
        mock.encode.side_effect = encode
        return mock

    def test_perfect_recall_on_identity_index(self):
        idx, entries = self._build_deterministic_index(10)
        model = self._one_hot_model(10)
        eval_rows = [(e.misconception_id, f"M{e.misconception_id}") for e in entries]
        results = evaluate_retrieval(idx, eval_rows, top_k=1, model=model)
        assert recall_at_k(results) == pytest.approx(1.0)

    def test_recall_at_k_empty_returns_zero(self):
        assert recall_at_k([]) == 0.0

    def test_row_has_correct_fields(self):
        idx, entries = self._build_deterministic_index(5)
        model = self._one_hot_model(5)
        results = evaluate_retrieval(idx, [(0, "M0")], top_k=3, model=model)
        row = results[0]
        assert isinstance(row, RetrievalEvalRow)
        assert row.true_misconception_id == 0
        assert isinstance(row.hit, bool)
        assert isinstance(row.retrieved_ids, list)

    def test_rank_is_none_when_not_retrieved(self):
        idx, entries = self._build_deterministic_index(10)
        model = self._one_hot_model(10)
        # Ask for M0 but query as if it's M9 — with top_k=1 and identity
        # embeddings, only M9 is returned.
        results = evaluate_retrieval(idx, [(0, "M9")], top_k=1, model=model)
        assert not results[0].hit
        assert results[0].rank is None
