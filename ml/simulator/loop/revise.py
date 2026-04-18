"""Revise step — HLR-driven daily revision selection.

For each previously-retrieved concept, compute the HLR predicted recall

    P(recall_c | now) = 2 ** (-hours_since_last_c / half_life_c)

and keep those in the "desirable difficulty" band (Bjork, 1994):

    MIN_RECALL <= P(recall) <= MAX_RECALL

Cap the list at `MAX_CONCEPTS` and sort by lowest recall first — the
concepts most in need of refresh come up before stronger ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ml.simulator.student.profile import StudentProfile

# Bjork's desirable-difficulty band: not so easy they add nothing,
# not so hard they fail. Spec values.
MIN_RECALL = 0.40
MAX_RECALL = 0.70
# Daily revision cap. Spec allows 3-8; we cap and let the caller decide
# what to do if fewer candidates exist.
MAX_CONCEPTS = 8


@dataclass(frozen=True)
class ReviseRecord:
    student_id: int
    concepts: tuple[int, ...]
    time: datetime


def _predict_recall(hours: float, half_life: float) -> float:
    if half_life <= 0.0:
        return 0.0
    return 2.0 ** (-max(hours, 0.0) / half_life)


def select_revision_concepts(
    profile: StudentProfile,
    now: datetime,
    min_recall: float = MIN_RECALL,
    max_recall: float = MAX_RECALL,
    max_concepts: int = MAX_CONCEPTS,
) -> list[int]:
    """Return concepts whose predicted recall sits in the desirable band."""
    candidates: list[tuple[int, float]] = []
    for concept_id, last_time in profile.last_retrieval.items():
        if last_time is None:
            continue
        hours = (now - last_time).total_seconds() / 3600.0
        half_life = profile.recall_half_life.get(concept_id, 24.0)
        recall = _predict_recall(hours, half_life)
        if min_recall <= recall <= max_recall:
            candidates.append((concept_id, recall))
    # Weakest first (lowest recall most in need), deterministic tiebreak by concept_id.
    candidates.sort(key=lambda x: (x[1], x[0]))
    return [c for c, _ in candidates[:max_concepts]]
