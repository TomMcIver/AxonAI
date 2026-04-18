"""Two-Parameter Logistic (2PL) IRT — Birnbaum (1968).

The 2PL model:

    P(correct | theta, a, b) = 1 / (1 + exp(-a * (theta - b)))

where:
    theta  — latent ability of the student
    a      — item discrimination (slope)
    b      — item difficulty (ability at which P = 0.5)

Pure functions; no data IO.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np


def prob_correct(theta: float, a: float, b: float) -> float:
    """Probability of a correct response under 2PL IRT.

    Numerically stable for large |a * (theta - b)| by branching on the
    sign of the exponent (avoids overflow in math.exp).
    """
    z = a * (theta - b)
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1.0 + exp_z)


def sample_response(theta: float, a: float, b: float, rng: np.random.Generator) -> bool:
    """Draw a Bernoulli response with P = prob_correct(theta, a, b)."""
    return bool(rng.random() < prob_correct(theta, a, b))


def log_likelihood(
    responses: Sequence[bool],
    thetas: Sequence[float],
    params: Sequence[Tuple[float, float]],
) -> float:
    """Sum of log-likelihoods over aligned (response, theta, (a, b)) triples.

    Uses logaddexp for numerical stability — equivalent to
        log P(correct) = -log(1 + exp(-z))
        log P(wrong)   = -log(1 + exp( z))
    with z = a * (theta - b).
    """
    if not (len(responses) == len(thetas) == len(params)):
        raise ValueError("responses, thetas, params must be the same length")

    resp = np.asarray(responses, dtype=bool)
    theta_arr = np.asarray(thetas, dtype=float)
    params_arr = np.asarray(params, dtype=float)  # shape (n, 2)
    a_arr = params_arr[:, 0]
    b_arr = params_arr[:, 1]

    z = a_arr * (theta_arr - b_arr)
    log_p = -np.logaddexp(0.0, -z)   # log P(correct)
    log_q = -np.logaddexp(0.0, z)    # log P(wrong)

    return float(np.where(resp, log_p, log_q).sum())
