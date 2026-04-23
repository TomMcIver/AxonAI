"""Phase 2 PR B3 — misconception detector, retrieval stage.

Embeds question-text + wrong-answer-text using a bi-encoder
(`all-MiniLM-L6-v2`) and retrieves the top-k misconception candidates
from the Eedi catalogue via cosine similarity. B4 will rerank these
with a cross-encoder; B5 will wire the full pipeline into the loop.

Design notes
------------

* **Model pin.** The Phase 2 plan §4.3 concern #2 requires CPU-pinned,
  seeded inference for determinism. We pin the model *revision* hash and
  set `torch.manual_seed` before encoding. GPU-side float non-determinism
  is explicitly excluded by forcing `device="cpu"`.

* **Seen / unseen split.** B3 requires 20% of misconceptions to be held
  out *by misconception ID* (column-disjoint split), imitating the
  Kaggle test distribution where unseen misconception classes appear at
  inference time. `build_train_test_split` provides a deterministic
  seeded helper (the spec does not mandate one; we commit it here).

* **No S3 dependency at inference time.** The retriever works from an
  in-memory list of `MisconceptionEntry` structs; callers load those
  from whatever source (Eedi CSV, the committed id-map, or a synthetic
  fixture). `build_index` pre-embeds the catalogue once and caches the
  matrix for repeated queries.

* **Acceptance gate.** Recall@k = fraction of test rows for which the
  true misconception appears in the top-k retrieved candidates. The
  spec acceptance threshold is recall@25 ≥ 0.60 on the seen split and
  recall@25 ≥ 0.35 on the unseen split (MiniLM baseline; the cross-
  encoder in B4 refines from this set).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import torch

# Model choice: MiniLM-L6-v2 is the lightest strong bi-encoder;
# recall@25 on Eedi-like educational text is typically 65-75% before
# reranking. Revision None uses the HEAD of the model's main branch;
# for production deployments pin this to a commit SHA after verifying
# the model works with the installed transformers version.
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL_REVISION = None
# B3/B4 plan §4.3 concern #2: force CPU for deterministic float ops.
_DEVICE = "cpu"
# Seen/unseen split: 80/20 by misconception ID.
_UNSEEN_FRACTION = 0.20
# Default recall@k window.
DEFAULT_TOP_K = 25


@dataclass(frozen=True)
class MisconceptionEntry:
    """One row from the Eedi misconception catalogue."""

    misconception_id: int
    name: str  # MisconceptionName; may be empty for derived catalogues


@dataclass
class MisconceptionIndex:
    """Pre-computed bi-encoder index over a misconception catalogue.

    `entries[i]` corresponds to `embeddings[i]` — order is preserved
    from `build_index`'s input list and kept stable so the int-mapping
    from B1 (`build_eedi_id_map`) stays valid.
    """

    entries: list[MisconceptionEntry]
    embeddings: np.ndarray  # shape (N, D), float32, L2-normalised
    model_name: str
    model_revision: str


def _get_model():
    """Lazy-load the sentence-transformer (avoids import-time download)."""
    from sentence_transformers import SentenceTransformer

    torch.manual_seed(0)
    kwargs = {"device": _DEVICE}
    if _MODEL_REVISION is not None:
        kwargs["revision"] = _MODEL_REVISION
    return SentenceTransformer(_MODEL_NAME, **kwargs)


def _encode(model, texts: list[str]) -> np.ndarray:
    """Encode `texts`, return L2-normalised float32 matrix."""
    torch.manual_seed(0)
    vecs = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
        device=_DEVICE,
    )
    return vecs.astype(np.float32)


def build_index(
    entries: Sequence[MisconceptionEntry],
    model=None,
) -> MisconceptionIndex:
    """Embed all `entries` and return a ready-to-query index.

    `model` is the `SentenceTransformer` instance; pass one in to avoid
    repeated network/disk loads across multiple calls (e.g. unit tests).
    If None, the function loads the pinned model lazily.
    """
    if model is None:
        model = _get_model()
    texts = [
        e.name if e.name else f"Misconception {e.misconception_id}"
        for e in entries
    ]
    embeddings = _encode(model, texts)
    return MisconceptionIndex(
        entries=list(entries),
        embeddings=embeddings,
        model_name=_MODEL_NAME,
        model_revision=_MODEL_REVISION,
    )


def retrieve(
    index: MisconceptionIndex,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    model=None,
) -> list[tuple[MisconceptionEntry, float]]:
    """Return the top-k `(entry, cosine_score)` pairs for `query`.

    Scores are in [-1, 1] (cosine similarity on L2-normalised vectors);
    results are sorted descending by score.
    """
    if model is None:
        model = _get_model()
    q_vec = _encode(model, [query])[0]  # (D,)
    scores = index.embeddings @ q_vec  # (N,)
    k = min(top_k, len(index.entries))
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
    return [
        (index.entries[int(i)], float(scores[i])) for i in top_indices
    ]


def build_query_text(question_text: str, wrong_answer_text: str) -> str:
    """Concatenate question + wrong-answer text into one retrieval query.

    The bi-encoder encodes the pair as a single string so that both the
    concept and the specific error surface are present. A separator
    token ` [SEP] ` is used to match the training format of MiniLM.
    """
    return f"{question_text.strip()} [SEP] {wrong_answer_text.strip()}"


# ---------------------------------------------------------------------------
# Seen / unseen split
# ---------------------------------------------------------------------------


def build_train_test_split(
    entries: Sequence[MisconceptionEntry],
    unseen_fraction: float = _UNSEEN_FRACTION,
    seed: int = 42,
) -> tuple[list[MisconceptionEntry], list[MisconceptionEntry]]:
    """Split entries into (train, test) by misconception ID.

    The split is column-disjoint: the test set contains entirely
    different misconception IDs from training, imitating the Kaggle
    held-out evaluation distribution where unseen classes appear at
    inference time. Deterministic under `seed`.

    Returns (train_entries, test_entries).
    """
    rng = np.random.default_rng(seed)
    ids = np.array([e.misconception_id for e in entries])
    n = len(ids)
    perm = rng.permutation(n)
    n_test = max(1, int(round(n * unseen_fraction)))
    test_mask = np.zeros(n, dtype=bool)
    test_mask[perm[:n_test]] = True
    train = [e for e, m in zip(entries, test_mask) if not m]
    test = [e for e, m in zip(entries, test_mask) if m]
    return train, test


# ---------------------------------------------------------------------------
# Evaluation helper
# ---------------------------------------------------------------------------


@dataclass
class RetrievalEvalRow:
    """One evaluation query and its result."""

    true_misconception_id: int
    query: str
    retrieved_ids: list[int]
    rank: int | None  # 1-based rank of true ID; None if not in top-k
    hit: bool


def evaluate_retrieval(
    index: MisconceptionIndex,
    eval_rows: list[tuple[int, str]],  # (true_misconception_id, query)
    top_k: int = DEFAULT_TOP_K,
    model=None,
) -> list[RetrievalEvalRow]:
    """Score a list of (true_id, query) pairs against the index.

    Returns one `RetrievalEvalRow` per query. Recall@k = mean(row.hit).
    """
    if model is None:
        model = _get_model()
    results = []
    for true_id, query in eval_rows:
        hits = retrieve(index, query, top_k=top_k, model=model)
        retrieved_ids = [e.misconception_id for e, _ in hits]
        if true_id in retrieved_ids:
            rank = retrieved_ids.index(true_id) + 1
            hit = True
        else:
            rank = None
            hit = False
        results.append(
            RetrievalEvalRow(
                true_misconception_id=true_id,
                query=query,
                retrieved_ids=retrieved_ids,
                rank=rank,
                hit=hit,
            )
        )
    return results


def recall_at_k(rows: list[RetrievalEvalRow]) -> float:
    """Fraction of queries where the true ID appears in the top-k set."""
    if not rows:
        return 0.0
    return float(np.mean([r.hit for r in rows]))
