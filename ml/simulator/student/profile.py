"""Student state carried through the simulation.

`StudentProfile` is the single mutable payload the loop threads through.
It bundles:

- Ground truth (hidden from the student-facing model): per-concept
  `true_theta`, plus the student's trait parameters drawn from priors.
- Observable/latent state used by the tutor: `estimated_theta` (mean,
  var), `bkt_state`, `elo_rating`, `recall_half_life`, `last_retrieval`.
- History: flat `attempts_history` list of `AttemptRecord`s.
- A `misconception_susceptibility` dict that stays empty in v1 — it's a
  seam for v2 to weight distractor selection.

The profile is a plain dataclass; `ml.simulator.student.dynamics`
returns fresh instances (functional style) after each practice/forgetting
step so downstream code gets immutability semantics without the pain of
making every nested dict frozen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ml.simulator.psychometrics.bkt import BKTState


@dataclass(frozen=True)
class AttemptRecord:
    """One response the student produced during the simulation."""

    concept_id: int
    item_id: int
    is_correct: bool
    time: datetime
    response_time_ms: int
    # Pedagogical style the tutor framed the item in before the student
    # answered (see `ml.simulator.loop.explanation_style`). Optional for
    # Phase 1 fixtures that predate the B6 selector.
    explanation_style: Optional[str] = None
    # Misconception ID of the distractor the student chose when wrong
    # (see `ml.simulator.misconception.response_model`). None when the
    # student was correct, or when the item has no distractor metadata.
    triggered_misconception_id: Optional[int] = None


@dataclass
class StudentProfile:
    """Complete state for a single synthetic student."""

    student_id: int
    true_theta: dict[int, float]
    estimated_theta: dict[int, tuple[float, float]]
    bkt_state: dict[int, BKTState]
    elo_rating: float
    recall_half_life: dict[int, float]
    last_retrieval: dict[int, datetime]
    learning_rate: float
    slip: float
    guess: float
    engagement_decay: float
    response_time_lognorm_params: tuple[float, float]
    attempts_history: list[AttemptRecord] = field(default_factory=list)
    misconception_susceptibility: dict[int, float] = field(default_factory=dict)

    def attempts_on(self, concept_id: Optional[int] = None) -> int:
        """Count of attempts, optionally filtered to one concept."""
        if concept_id is None:
            return len(self.attempts_history)
        return sum(1 for r in self.attempts_history if r.concept_id == concept_id)
