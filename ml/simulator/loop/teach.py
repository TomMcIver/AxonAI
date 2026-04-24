"""Teach step.

v1 was intentionally minimal. B7 extends this with an optional LLM tutor
call: when `llm_tutor` and `explanation_style` are both provided, the tutor
generates a short explanation that is stored in `TeachRecord.llm_explanation`.

No direct change to `true_theta` — learning happens during quiz/revise
practice. `last_retrieval[concept_id]` is set to `now` so HLR treats
concept exposure as an initial retrieval event.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from ml.simulator.student.profile import StudentProfile

if TYPE_CHECKING:
    from ml.simulator.loop.llm_tutor import LLMTutor


@dataclass(frozen=True)
class TeachRecord:
    student_id: int
    concept_id: int
    time: datetime
    # B7: explanation style used for this teach event (None in v1 / no tutor).
    explanation_style: str | None = None
    # B7: LLM-generated explanation text (None when no tutor or API failure).
    llm_explanation: str | None = None
    # Invariant: always True for simulator-generated records.
    is_simulated: bool = True


def teach(
    profile: StudentProfile,
    concept_id: int,
    now: datetime,
    explanation_style: str | None = None,
    llm_tutor: "LLMTutor | None" = None,
) -> tuple[StudentProfile, TeachRecord]:
    """Mark the concept as taught and return (new_profile, record).

    When `llm_tutor` and `explanation_style` are both supplied, calls
    `llm_tutor.generate_explanation` and stores the result in the record.
    Any API exception is caught inside `LLMTutor.generate_explanation` and
    returns an empty string, so the loop always progresses.
    """
    last_new = dict(profile.last_retrieval)
    last_new[concept_id] = now
    new_profile = replace(profile, last_retrieval=last_new)

    llm_explanation: str | None = None
    if llm_tutor is not None and explanation_style is not None:
        llm_explanation = llm_tutor.generate_explanation(
            concept_id=concept_id,
            explanation_style=explanation_style,
        ) or None  # treat empty string as None

    record = TeachRecord(
        student_id=profile.student_id,
        concept_id=concept_id,
        time=now,
        explanation_style=explanation_style,
        llm_explanation=llm_explanation,
    )
    return new_profile, record
