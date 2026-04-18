"""Pure-function update rules applied to a `StudentProfile`.

These functions never mutate their inputs; each returns a new
`StudentProfile`. The loop module (PR 8) calls `apply_practice` on every
response and `apply_forgetting` whenever simulated time advances.

`apply_practice(profile, item_id, concept_id, is_correct, item_rating,
bkt_params, now, response_time_ms) -> (StudentProfile, float)`

- Adjusts `true_theta[concept_id]` by ±`learning_rate` (positive on
  correct, a dampened negative on wrong — knowledge decay is smaller
  than knowledge gain, following standard IRT/PFA practice).
- Updates the BKT posterior via `bkt.update`.
- Updates the student's global Elo and returns the new item Elo (the
  bank owns the item rating).
- Grows/shrinks `recall_half_life[concept_id]` via `hlr.update_half_life`.
- Records the attempt in `attempts_history` and resets
  `last_retrieval[concept_id] = now`.

`apply_forgetting(profile, now) -> StudentProfile`

- Decays every concept's `true_theta` toward a floor based on the
  retrieval-probability curve `2^(-hours/half_life)`. Half-life itself
  does not move in this step (half-life only updates on retrieval).
- Leaves `last_retrieval` untouched (that only shifts on practice).
"""

from __future__ import annotations

from copy import copy
from dataclasses import replace
from datetime import datetime

from ml.simulator.psychometrics import bkt as bkt_module
from ml.simulator.psychometrics import elo as elo_module
from ml.simulator.psychometrics import hlr as hlr_module
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.profile import AttemptRecord, StudentProfile

# Wrong responses decay true theta by this fraction of the learning rate.
# Smaller than the +1.0 gain on correct answers because forgetting via
# failure is weaker than encoding on success (Pavlik & Anderson, 2008).
_WRONG_DECAY_FRACTION = 0.5
# True-theta bounds (keep consistent with IRT calibrator + generator).
_THETA_LOWER = -4.0
_THETA_UPPER = 4.0
# Absorbing floor for forgetting. A fully-idle concept drifts toward this
# (not toward zero) so the student doesn't erase all prior knowledge.
_FORGETTING_FLOOR = -2.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def apply_practice(
    profile: StudentProfile,
    item_id: int,
    concept_id: int,
    is_correct: bool,
    item_rating: float,
    bkt_params: BKTParams,
    now: datetime,
    response_time_ms: int = 0,
) -> tuple[StudentProfile, float]:
    """Apply every practice-driven update. Returns (profile', item_rating')."""
    # true theta bump.
    theta_new = dict(profile.true_theta)
    delta = profile.learning_rate if is_correct else -_WRONG_DECAY_FRACTION * profile.learning_rate
    theta_new[concept_id] = _clamp(
        theta_new.get(concept_id, 0.0) + delta, _THETA_LOWER, _THETA_UPPER
    )

    # BKT posterior.
    bkt_new = dict(profile.bkt_state)
    prev_state = bkt_new.get(concept_id, BKTState(p_known=bkt_params.p_init))
    bkt_new[concept_id] = bkt_module.update(prev_state, is_correct, bkt_params)

    # Elo (student vs item).
    k = elo_module.k_factor(profile.attempts_on())
    new_student_rating, new_item_rating = elo_module.update(
        profile.elo_rating, item_rating, is_correct, k
    )

    # HLR half-life.
    hl_new = dict(profile.recall_half_life)
    current_hl = hl_new.get(concept_id, 24.0)
    hl_new[concept_id] = hlr_module.update_half_life(
        current_hl, is_correct, response_time_ms, features={}
    )

    # Last-retrieval + history append.
    last_new = dict(profile.last_retrieval)
    last_new[concept_id] = now
    history_new = list(profile.attempts_history)
    history_new.append(
        AttemptRecord(
            concept_id=concept_id,
            item_id=item_id,
            is_correct=is_correct,
            time=now,
            response_time_ms=response_time_ms,
        )
    )

    new_profile = replace(
        profile,
        true_theta=theta_new,
        bkt_state=bkt_new,
        elo_rating=new_student_rating,
        recall_half_life=hl_new,
        last_retrieval=last_new,
        attempts_history=history_new,
    )
    return new_profile, new_item_rating


def apply_forgetting(profile: StudentProfile, now: datetime) -> StudentProfile:
    """Decay `true_theta` forward from each concept's last retrieval.

    For each concept with a recorded last retrieval, compute
    `factor = 2^(-hours_since_last / half_life)` and move the concept's
    theta along the interval [`_FORGETTING_FLOOR`, theta_old]:

        theta_new = floor + (theta_old − floor) · factor

    Concepts never practised (no `last_retrieval` entry) are left
    untouched. Half-life and last-retrieval are not modified.
    """
    if not profile.last_retrieval:
        return replace(profile, true_theta=copy(profile.true_theta))

    theta_new = dict(profile.true_theta)
    for concept_id, last_time in profile.last_retrieval.items():
        if last_time is None:
            continue
        hours = max((now - last_time).total_seconds() / 3600.0, 0.0)
        hl = profile.recall_half_life.get(concept_id, 24.0)
        if hl <= 0.0:
            continue
        factor = hlr_module.predict_recall(hl, hours)
        current = theta_new.get(concept_id, 0.0)
        theta_new[concept_id] = _FORGETTING_FLOOR + (current - _FORGETTING_FLOOR) * factor

    return replace(profile, true_theta=theta_new)
