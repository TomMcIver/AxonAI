"""Phase 2 PR B10 — rewriter sample-testing harness.

Runs a sample of items from the item bank through the B8 rewriter and B9
verifier pipeline and reports aggregate quality statistics. Used during
the B11 integration run to gate whether the rewritten items are safe to
use in the simulation (pass rate must meet an acceptance threshold).

Entry points
------------

`run_harness(items, rewriter, verifier, ...)` — core function. Accepts
any iterable of `Item`s (already sampled or the full bank) and returns a
`HarnessReport`.

`sample_items(bank, n_samples, seed)` — draws `n_samples` items from an
`ItemBank` without replacement. Pass `n_samples=None` to use all items.

`HarnessReport` — structured result carrying per-item records and
aggregate metrics (pass rate, mean confidence, confidence histogram).

Acceptance criterion (B11 gate)
--------------------------------

A harness run is considered "passed" when `HarnessReport.pass_rate` is
≥ `acceptance_threshold` (default 0.80). The B11 integration script
asserts this before injecting rewritten items into the simulation loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.loop.rewriter import QuestionRewriter, RewriteRecord
from ml.simulator.loop.verifier import RewriteVerifier, VerificationResult

_DEFAULT_ACCEPTANCE_THRESHOLD = 0.80
_DEFAULT_CONFIDENCE_THRESHOLD = 0.70
_HISTOGRAM_N_BINS = 5


@dataclass(frozen=True)
class ItemHarnessRecord:
    """Rewrite + verification outcome for one item."""

    item: Item
    rewrite_record: RewriteRecord
    verification: VerificationResult


@dataclass(frozen=True)
class HarnessReport:
    """Aggregate result of a harness run.

    Attributes
    ----------
    n_sampled:
        Number of items sent through the pipeline.
    n_equivalent:
        Items whose rewrite was verified equivalent with confidence ≥ threshold.
    n_non_equivalent:
        Items verified as NOT equivalent (could be a bad rewrite).
    n_low_confidence:
        Items where the verifier's confidence was below the threshold and
        the result was excluded from the equivalent/non_equivalent counts.
    pass_rate:
        n_equivalent / n_sampled (0.0 when n_sampled == 0).
    mean_confidence:
        Mean verifier confidence across all items (including low-confidence).
    confidence_histogram:
        Counts per equal-width bin across [0, 1] with _HISTOGRAM_N_BINS bins.
        Length is always _HISTOGRAM_N_BINS.
    records:
        Per-item records (rewrite + verification pair).
    passed:
        True when pass_rate >= acceptance_threshold.
    """

    n_sampled: int
    n_equivalent: int
    n_non_equivalent: int
    n_low_confidence: int
    pass_rate: float
    mean_confidence: float
    confidence_histogram: tuple[int, ...]
    records: tuple[ItemHarnessRecord, ...]
    passed: bool


def sample_items(
    bank: ItemBank,
    n_samples: int | None = None,
    seed: int = 42,
) -> list[Item]:
    """Draw up to `n_samples` items from `bank` without replacement.

    When `n_samples` is None or exceeds the bank size, all items are returned
    in a deterministic shuffled order (seeded with `seed`).
    """
    all_items = bank.items()
    rng = np.random.default_rng(seed)
    if n_samples is None or n_samples >= len(all_items):
        indices = rng.permutation(len(all_items))
        return [all_items[i] for i in indices]
    indices = rng.choice(len(all_items), size=n_samples, replace=False)
    return [all_items[i] for i in indices]


def _confidence_histogram(confidences: Sequence[float], n_bins: int) -> tuple[int, ...]:
    """Build an equal-width histogram over [0, 1] with `n_bins` bins."""
    counts = [0] * n_bins
    for c in confidences:
        bin_idx = min(int(c * n_bins), n_bins - 1)
        counts[bin_idx] += 1
    return tuple(counts)


def run_harness(
    items: Sequence[Item],
    rewriter: QuestionRewriter,
    verifier: RewriteVerifier,
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
    acceptance_threshold: float = _DEFAULT_ACCEPTANCE_THRESHOLD,
    concept_description_map: dict[int, str] | None = None,
) -> HarnessReport:
    """Run the rewrite → verify pipeline on `items` and return a `HarnessReport`.

    Parameters
    ----------
    items:
        Items to process (use `sample_items` to draw from an `ItemBank`).
    rewriter:
        B8 `QuestionRewriter` instance.
    verifier:
        B9 `RewriteVerifier` instance.
    confidence_threshold:
        Verifier confidence below this is counted as `n_low_confidence`
        and excluded from `n_equivalent` / `n_non_equivalent`.
    acceptance_threshold:
        `HarnessReport.passed` is True when pass_rate ≥ this value.
    concept_description_map:
        Optional mapping from concept_id → human-readable description,
        forwarded to `rewriter.rewrite_item`. When None, synthetic
        placeholders from the B8 fallback are used.
    """
    harness_records: list[ItemHarnessRecord] = []
    all_confidences: list[float] = []
    n_equivalent = 0
    n_non_equivalent = 0
    n_low_confidence = 0

    cdm = concept_description_map or {}

    for item in items:
        concept_desc = cdm.get(item.concept_id)
        rewrite_rec = rewriter.rewrite_item(item, concept_description=concept_desc)
        verification = verifier.verify(rewrite_rec)

        all_confidences.append(verification.confidence)

        if verification.confidence < confidence_threshold:
            n_low_confidence += 1
        elif verification.is_equivalent:
            n_equivalent += 1
        else:
            n_non_equivalent += 1

        harness_records.append(
            ItemHarnessRecord(
                item=item,
                rewrite_record=rewrite_rec,
                verification=verification,
            )
        )

    n_sampled = len(items)
    pass_rate = n_equivalent / n_sampled if n_sampled > 0 else 0.0
    mean_confidence = float(np.mean(all_confidences)) if all_confidences else 0.0
    histogram = _confidence_histogram(all_confidences, _HISTOGRAM_N_BINS)

    return HarnessReport(
        n_sampled=n_sampled,
        n_equivalent=n_equivalent,
        n_non_equivalent=n_non_equivalent,
        n_low_confidence=n_low_confidence,
        pass_rate=pass_rate,
        mean_confidence=mean_confidence,
        confidence_histogram=histogram,
        records=tuple(harness_records),
        passed=pass_rate >= acceptance_threshold,
    )
