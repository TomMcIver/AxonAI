"""Phase 2 PR B5 — misconception detector, loop integration.

Wraps the B3 (retrieval) + B4 (rerank) pipeline into a single
`MisconceptionDetector` that the `TermRunner` calls before each attempt
to produce a `DetectorHint` for the B6 explanation-style selector.

Two operating modes
-------------------

**Tagged shortcut** (default, `use_tagged_shortcut=True`):

  When the item has curator-tagged distractors (`Item.distractors` with
  non-None `misconception_id`), the detector skips the bi-encoder and
  finds the tagged misconception whose susceptibility weight in the
  student's profile is highest. Confidence = that susceptibility weight.
  If the student has zero susceptibility for all tagged misconceptions,
  the function returns None (no meaningful hint).

  This fast path avoids a per-item forward pass during simulation and
  produces high-quality predictions for items that have Eedi curation.

**Full retrieval path** (requires `retrieval_index` and models to be set):

  Runs B3 `retrieve` + B4 `rerank` on a query built from the item's
  question text. Since `Item` in the current simulator carries distractor
  option text but not the question stem, this path is reserved for B11's
  full-data integration run where `Item` may be extended. Until then,
  calling `predict` without a `retrieval_index` on an item without tags
  returns None with a warning.

`TermRunner` wiring
-------------------

`TermRunner` grows an optional `misconception_detector` field. When set,
`_detector_hint_for` delegates to `detector.predict(profile, item)`
instead of returning None. The style selector (B6) then fires Rule 1
when the returned confidence ≥ its threshold.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from ml.simulator.data.item_bank import Item
from ml.simulator.loop.explanation_style import DetectorHint
from ml.simulator.student.profile import StudentProfile

# Minimum susceptibility weight required to report a tagged misconception
# as a hint. Below this the student essentially has no active link to
# that misconception and the hint would be noise. Matches B1's
# _WEIGHT_MIN (0.20) floor — anything B1 generates is above this.
_MIN_SUSCEPTIBILITY_FOR_HINT = 0.10


@dataclass
class MisconceptionDetector:
    """Combines B3 retrieval + B4 rerank into a loop-time detector.

    Instantiate with the index and models from B3/B4 when running the
    full pipeline; leave them as None to use the tagged shortcut only.
    """

    # B3 index (pre-built via build_index). None → tagged shortcut only.
    retrieval_index: object | None = None  # MisconceptionIndex | None
    # Sentence-transformer bi-encoder (loaded by _get_model()).
    bi_model: object | None = None
    # Cross-encoder model (loaded by _get_ce_model()).
    ce_model: object | None = None
    # Top-k candidates retrieved before reranking.
    top_k: int = 25
    # Use curator-tagged distractors when available (fast path).
    use_tagged_shortcut: bool = True
    # Minimum CE logit to forward as a hint. -inf = accept all scores.
    confidence_threshold: float = float("-inf")
    # Minimum susceptibility weight to surface a tagged misconception.
    min_susceptibility: float = _MIN_SUSCEPTIBILITY_FOR_HINT

    def predict(
        self,
        profile: StudentProfile,
        item: Item,
    ) -> DetectorHint | None:
        """Return a `DetectorHint` or None.

        Tries the tagged shortcut first (if `use_tagged_shortcut` and
        the item has tagged distractors), then falls back to B3+B4 if a
        `retrieval_index` is set, otherwise returns None.
        """
        if self.use_tagged_shortcut and item.distractors:
            hint = self._from_tags(profile, item)
            if hint is not None:
                return hint

        if self.retrieval_index is not None:
            return self._from_retrieval(profile, item)

        return None

    def _from_tags(
        self, profile: StudentProfile, item: Item
    ) -> DetectorHint | None:
        """Fast path: find the highest-susceptibility tagged misconception."""
        best_id: int | None = None
        best_w = 0.0
        for d in item.distractors:
            mid = d.misconception_id
            if mid is None:
                continue
            w = profile.misconception_susceptibility.get(mid, 0.0)
            if w > best_w:
                best_w = w
                best_id = mid
        if best_id is None or best_w < self.min_susceptibility:
            return None
        return DetectorHint(misconception_id=best_id, confidence=best_w)

    def _from_retrieval(
        self, profile: StudentProfile, item: Item
    ) -> DetectorHint | None:
        """Full B3+B4 path. Requires retrieval_index + bi_model + ce_model."""
        from ml.simulator.misconception.retrieval import (
            build_query_text,
            retrieve,
            _get_model,
        )
        from ml.simulator.misconception.reranker import rerank, top_prediction

        # Prefer question text from the item if available; otherwise use
        # the distractor option texts as a proxy for the error pattern.
        # Current simulator Item does not carry question_text — this path
        # is fully exercised in B11's extended Item model.
        if not item.distractors:
            warnings.warn(
                f"MisconceptionDetector._from_retrieval: item {item.item_id} has no "
                "distractors and no question_text — cannot form a retrieval query. "
                "Returning None.",
                stacklevel=3,
            )
            return None

        # Use option text from all distractors as a proxy query.
        proxy_text = "; ".join(
            d.option_text for d in item.distractors if d.option_text
        )
        query = build_query_text(
            f"Item {item.item_id} (concept {item.concept_id})", proxy_text
        )
        bi_model = self.bi_model or _get_model()
        candidates = retrieve(
            self.retrieval_index, query, top_k=self.top_k, model=bi_model
        )
        if not candidates:
            return None

        ce_model = self.ce_model
        if ce_model is not None:
            from ml.simulator.misconception.reranker import rerank as _rerank
            candidates = _rerank(query, candidates, model=ce_model)

        entry, score = top_prediction(candidates, self.confidence_threshold)
        if entry is None:
            return None
        return DetectorHint(misconception_id=entry.misconception_id, confidence=float(score))
