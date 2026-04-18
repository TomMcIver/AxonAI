"""Teach step.

v1 is intentionally minimal: the tutor "presents" a concept to the
student, which in the simulator boils down to

    1. a `TeachRecord` event being emitted, and
    2. the student's `last_retrieval[concept_id]` being set to `now`
       (exposure counts as a retrieval for HLR purposes).

No LLM is invoked. No direct change to `true_theta` — learning happens
during `quiz` / `revise` practice. BKT state was already seeded by the
generator for every concept in the graph, so there is nothing to
initialise here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ml.simulator.student.profile import StudentProfile


@dataclass(frozen=True)
class TeachRecord:
    student_id: int
    concept_id: int
    time: datetime


def teach(
    profile: StudentProfile, concept_id: int, now: datetime
) -> tuple[StudentProfile, TeachRecord]:
    """Mark the concept as taught and return (new_profile, record)."""
    last_new = dict(profile.last_retrieval)
    last_new[concept_id] = now
    new_profile = replace(profile, last_retrieval=last_new)
    record = TeachRecord(
        student_id=profile.student_id, concept_id=concept_id, time=now
    )
    return new_profile, record
