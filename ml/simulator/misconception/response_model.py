"""Phase 2 PR B2 — misconception-weighted distractor selection.

When a simulated student answers incorrectly, the specific *wrong*
distractor they choose is no longer drawn uniformly at random (v1
behaviour). Instead the probability of choosing a distractor is
proportional to the student's `misconception_susceptibility` weight for
that distractor's tagged misconception ID.

Design
------

The logit-additive formulation: for a student with susceptibility weight
`w_m` for misconception `m`, and a distractor `d` tagged with `m`, the
selection weight for `d` is

    weight(d) = 1 + susceptibility_scale * w_m

Distractors with no misconception tag, or whose misconception is not in
the student's susceptibility map, have weight 1 (the uniform baseline).
This keeps the model additive: setting `misconception_susceptibility={}`
(Phase 1 fallback) produces exactly uniform distractor selection.

The parameter `susceptibility_scale` is a linear multiplier on how much
a non-zero susceptibility weight inflates the odds. With the default
value of 4.0, a student whose susceptibility weight for misconception m
is 0.5 (the midpoint of [0.2, 0.9] from B1) has a selection weight of
1 + 4.0 * 0.5 = 3.0 — three times more likely than a non-tagged
distractor. This matches the Phase 2 spec's intent that "active"
misconceptions materially skew wrong-answer choice without dominating
the correct-answer probability (which is governed by the IRT model
separately).

When the item has no distractors, or when the student answers correctly,
the function returns `None` — no misconception is triggered.

Constants
---------
Constants live here for the same reason as B1's — they parameterise a
published distribution shape, not a runtime knob.
"""

from __future__ import annotations

import numpy as np

from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.student.profile import StudentProfile

# Linear scale on susceptibility weight → distractor selection odds.
# See docstring; 4.0 means susceptibility = 0.5 triples the odds.
_SUSCEPTIBILITY_SCALE = 4.0


def select_distractor(
    item: Item,
    profile: StudentProfile,
    rng: np.random.Generator,
    susceptibility_scale: float = _SUSCEPTIBILITY_SCALE,
) -> tuple[Distractor | None, int | None]:
    """Pick a distractor when the student answers incorrectly.

    Returns `(chosen_distractor, triggered_misconception_id)`. Both are
    `None` when the item has no distractors (bare-bones items from
    ASSISTments that have no Eedi overlay).

    When `profile.misconception_susceptibility` is empty (Phase 1
    compatibility) the selection degrades to uniform-at-random.
    """
    if not item.distractors:
        return None, None

    weights = np.array(
        [
            1.0
            + susceptibility_scale
            * profile.misconception_susceptibility.get(
                d.misconception_id if d.misconception_id is not None else -1, 0.0
            )
            for d in item.distractors
        ],
        dtype=np.float64,
    )
    total = weights.sum()
    probs = weights / total

    idx = int(rng.choice(len(item.distractors), p=probs))
    chosen = item.distractors[idx]
    triggered_id = chosen.misconception_id
    return chosen, triggered_id
