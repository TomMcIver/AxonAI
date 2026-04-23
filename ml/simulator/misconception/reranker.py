"""Phase 2 PR B4 — misconception detector, cross-encoder rerank stage.

Takes the top-k candidates from B3's bi-encoder retrieval and reranks
them with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`),
which jointly encodes (query, candidate) pairs and returns a relevance
score. The reranker dramatically improves precision@1 at the cost of
O(k) forward passes per query.

Design
------

* **Model pin.** CPU-pinned, `torch.manual_seed(0)`, same determinism
  contract as B3 (plan §4.3 concern #2).
* **Input.** A query string (from `build_query_text`) and a list of
  `(MisconceptionEntry, score)` pairs from `retrieve`. The reranker
  re-scores each pair and re-sorts.
* **Output.** Same list structure — `list[(MisconceptionEntry, float)]`
  — sorted descending by cross-encoder score. Downstream code (B5) reads
  `result[0]` as the top prediction and `result[0][1]` as the confidence.
* **Acceptance gate.** Precision@1 ≥ 0.50 on the seen split. The
  cross-encoder is expected to improve substantially over the bi-encoder's
  top-1 precision while keeping recall@25 unchanged (since it only reranks
  the existing candidate set).

Constants
---------
The cross-encoder model name is the only constant here; all other
parameters (top_k, confidence threshold) belong to the caller because
they are loop-level policy, not model-level behaviour.
"""

from __future__ import annotations

import numpy as np
import torch

from ml.simulator.misconception.retrieval import MisconceptionEntry

_CE_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_DEVICE = "cpu"


def _get_ce_model():
    """Lazy-load the cross-encoder (avoids import-time download)."""
    from sentence_transformers import CrossEncoder

    torch.manual_seed(0)
    return CrossEncoder(_CE_MODEL_NAME, device=_DEVICE)


def rerank(
    query: str,
    candidates: list[tuple[MisconceptionEntry, float]],
    model=None,
) -> list[tuple[MisconceptionEntry, float]]:
    """Re-score `candidates` with a cross-encoder and return sorted descending.

    `candidates` is the output of `retrieve` — a list of
    `(MisconceptionEntry, bi_encoder_score)` pairs. The returned list
    replaces the bi-encoder score with the cross-encoder logit score and
    re-sorts. If `candidates` is empty, returns an empty list.
    """
    if not candidates:
        return []
    if model is None:
        model = _get_ce_model()

    torch.manual_seed(0)
    pairs = [
        (query, entry.name if entry.name else f"Misconception {entry.misconception_id}")
        for entry, _ in candidates
    ]
    scores = model.predict(pairs, show_progress_bar=False)
    scored = list(zip([e for e, _ in candidates], scores.tolist()))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def top_prediction(
    reranked: list[tuple[MisconceptionEntry, float]],
    confidence_threshold: float = float("-inf"),
) -> tuple[MisconceptionEntry | None, float]:
    """Return the top-ranked entry and its score, or (None, score) if below threshold.

    Cross-encoder outputs raw logits (unbounded, may be negative), so the
    default threshold is -inf (accept everything). B5 should tune this to
    a calibrated operating point after evaluating on held-out data.
    """
    if not reranked:
        return None, 0.0
    top_entry, top_score = reranked[0]
    if top_score < confidence_threshold:
        return None, float(top_score)
    return top_entry, float(top_score)


# ---------------------------------------------------------------------------
# Evaluation helper
# ---------------------------------------------------------------------------


def evaluate_rerank(
    reranked_results: list[tuple[int, list[tuple[MisconceptionEntry, float]]]],
) -> dict[str, float]:
    """Score reranked results; input is list of (true_id, reranked_list).

    Returns dict with keys: precision_at_1, mrr (mean reciprocal rank),
    n_queries.
    """
    if not reranked_results:
        return {"precision_at_1": 0.0, "mrr": 0.0, "n_queries": 0}

    p1_hits = []
    rr_vals = []
    for true_id, ranked in reranked_results:
        ids = [e.misconception_id for e, _ in ranked]
        hit1 = len(ids) > 0 and ids[0] == true_id
        p1_hits.append(float(hit1))
        if true_id in ids:
            rank = ids.index(true_id) + 1
            rr_vals.append(1.0 / rank)
        else:
            rr_vals.append(0.0)

    return {
        "precision_at_1": float(np.mean(p1_hits)),
        "mrr": float(np.mean(rr_vals)),
        "n_queries": len(reranked_results),
    }
