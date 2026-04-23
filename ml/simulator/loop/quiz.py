"""Quiz step — ZPD item selection and 2PL response simulation.

`select_next_item` picks an item whose predicted P(correct) sits in the
ZPD band `[ZPD_LOWER, ZPD_UPPER]` given the student's current true θ on
that concept. The band is Vygotsky's "zone of proximal development"
applied to adaptive testing (Pelánek 2016, §3.2). Ties are broken by
distance to the band centre.

`simulate_response` draws a Bernoulli correctness from the 2PL
probability and a log-normal response time from the student's priors.
Returns `(is_correct, response_time_ms)`. Distractor choice is not
modelled in v1 — the `Item.distractors` structure is carried for v2 use
(misconception-weighted wrong-answer selection).
"""

from __future__ import annotations

from typing import Optional

import math
import numpy as np

from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.misconception.response_model import select_distractor
from ml.simulator.psychometrics.irt_2pl import prob_correct
from ml.simulator.student.profile import StudentProfile

# ZPD target band. Spec: 0.60 <= P(correct) <= 0.85 keeps practice in
# the "productive struggle" regime.
ZPD_LOWER = 0.60
ZPD_UPPER = 0.85
_ZPD_CENTRE = (ZPD_LOWER + ZPD_UPPER) / 2.0


def select_next_item(
    profile: StudentProfile,
    item_bank: ItemBank,
    concept_id: int,
    lower: float = ZPD_LOWER,
    upper: float = ZPD_UPPER,
) -> Optional[Item]:
    """Return the best-matching item for practice, or None if none exist."""
    items = item_bank.items_for_concept(concept_id)
    if not items:
        return None
    theta = profile.true_theta.get(concept_id, 0.0)
    centre = (lower + upper) / 2.0
    best: Optional[Item] = None
    best_distance = math.inf
    for item in items:
        p = prob_correct(theta, item.a, item.b)
        if lower <= p <= upper:
            # Any in-band item with distance to the centre is candidate.
            distance = abs(p - centre)
        else:
            distance = min(abs(p - lower), abs(p - upper)) + 1.0  # penalty
        if distance < best_distance:
            best_distance = distance
            best = item
    return best


def simulate_response(
    profile: StudentProfile,
    item: Item,
    rng: np.random.Generator,
) -> tuple[bool, int, int | None]:
    """Draw a 2PL response + log-normal RT + triggered misconception ID.

    Returns `(is_correct, response_time_ms, triggered_misconception_id)`.
    `triggered_misconception_id` is the misconception ID of the distractor
    chosen when wrong (B2 misconception-weighted selection), or None when
    the student is correct or the item has no distractor metadata.
    """
    theta = profile.true_theta.get(item.concept_id, 0.0)
    p = prob_correct(theta, item.a, item.b)
    is_correct = bool(rng.random() < p)
    mu, sigma = profile.response_time_lognorm_params
    if sigma > 0.0:
        response_time_ms = int(np.exp(rng.normal(mu, sigma)))
    else:
        response_time_ms = int(np.exp(mu))
    # B2: when wrong, select a distractor weighted by misconception susceptibility.
    triggered_misconception_id: int | None = None
    if not is_correct:
        _, triggered_misconception_id = select_distractor(item, profile, rng)
    # Guard: response time should never be zero or negative.
    return is_correct, max(response_time_ms, 1), triggered_misconception_id
