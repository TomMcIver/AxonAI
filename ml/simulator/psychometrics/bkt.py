"""Bayesian Knowledge Tracing — Corbett & Anderson (1995).

Four parameters per skill:
    p_init     — P(known) before any practice
    p_transit  — P(learn on this opportunity | not known)
    p_slip     — P(wrong | known)
    p_guess    — P(correct | not known)

Observation model:
    P(correct | known)      = 1 - p_slip
    P(correct | not known)  = p_guess

Update rule: Bayesian posterior over the latent (known / not-known) state,
followed by the learning transition. Pure functions; no data IO.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    """Per-skill BKT parameters.

    Degeneracy constraint (Beck & Chang, 2007): p_slip + p_guess < 1.
    Violations are permitted here; calibrator enforces in PR 5.
    """

    p_init: float
    p_transit: float
    p_slip: float
    p_guess: float


@dataclass(frozen=True)
class BKTState:
    """Posterior probability the skill is currently known."""

    p_known: float


def predict_correct(state: BKTState, params: BKTParams) -> float:
    """Probability the next response on this skill is correct.

        P(correct) = P(known) * (1 - p_slip) + (1 - P(known)) * p_guess
    """
    k = state.p_known
    return k * (1.0 - params.p_slip) + (1.0 - k) * params.p_guess


def update(state: BKTState, is_correct: bool, params: BKTParams) -> BKTState:
    """Bayesian posterior over 'known' given the observation, then learn.

    Step 1 — posterior over the latent state at the time of the response:

        If correct:
            P(K | correct) = P(K) * (1 - S)
                           / [P(K) * (1 - S) + (1 - P(K)) * G]
        If wrong:
            P(K | wrong)   = P(K) * S
                           / [P(K) * S + (1 - P(K)) * (1 - G)]

    Step 2 — learning transition after the observation:

        P(K_{t+1}) = P(K | obs) + (1 - P(K | obs)) * p_transit
    """
    k = state.p_known
    s = params.p_slip
    g = params.p_guess

    if is_correct:
        num = k * (1.0 - s)
        denom = num + (1.0 - k) * g
    else:
        num = k * s
        denom = num + (1.0 - k) * (1.0 - g)

    # Edge case: observation has zero probability under the prior — fall
    # back to the prior rather than divide by zero.
    posterior = num / denom if denom > 0.0 else k
    p_known_next = posterior + (1.0 - posterior) * params.p_transit
    return BKTState(p_known=p_known_next)
