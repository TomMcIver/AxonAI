"""Half-Life Regression retention — Settles & Meeder (2016), Duolingo.

Memory strength is parameterised by a half-life (in hours). Probability
of recall decays exponentially:

    P(recall) = 2 ** (-hours_since_last / half_life_hours)

On a successful retrieval the half-life grows (Leitner-style, 1972); on a
lapse it shrinks. Growth/decay factors are trainable in the full HLR
model; v1 uses Leitner defaults (×2 on correct, ×0.5 on wrong), overridable
via the `features` dict.

Pure functions; no data IO.
"""

from __future__ import annotations

# Leitner-style default spacing factors (Leitner, 1972). Final values
# move to config.py in a later PR.
_DEFAULT_GROWTH_CORRECT = 2.0
_DEFAULT_GROWTH_WRONG = 0.5

# Clamp the minimum half-life (hours) to prevent numerical collapse when
# a student chains many wrong answers. 15 minutes is short enough to be
# effectively zero without underflowing the 2 ** (-t/hl) path.
_MIN_HALF_LIFE_HOURS = 0.25


def predict_recall(half_life_hours: float, hours_since_last: float) -> float:
    """Probability of correctly recalling the concept now.

    Defined for half_life_hours > 0 and hours_since_last >= 0.
    """
    if half_life_hours <= 0.0:
        raise ValueError("half_life_hours must be positive")
    if hours_since_last < 0.0:
        raise ValueError("hours_since_last must be non-negative")
    return 2.0 ** (-hours_since_last / half_life_hours)


def update_half_life(
    current_hl: float,
    is_correct: bool,
    response_time_ms: int,
    features: dict,
) -> float:
    """Update the half-life given the latest retrieval outcome.

    `response_time_ms` is accepted for interface compatibility with the
    Duolingo HLR model (faster correct retrievals → stronger memory) but
    is not consumed by the v1 rule. `features` may override the default
    growth factors:

        'growth_correct'  (float, defaults to 2.0)
        'growth_wrong'    (float, defaults to 0.5)

    Calibration in PR 5 may fit a richer per-concept model here.
    """
    if is_correct:
        growth = features.get("growth_correct", _DEFAULT_GROWTH_CORRECT)
    else:
        growth = features.get("growth_wrong", _DEFAULT_GROWTH_WRONG)
    return max(current_hl * growth, _MIN_HALF_LIFE_HOURS)
