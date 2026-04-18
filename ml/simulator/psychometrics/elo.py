"""Elo rating for adaptive educational systems — Pelánek (2016).

Student and question each carry a rating on the standard Elo scale.
Expected score is logistic in the rating difference with a scale of 400
(FIDE convention). Ratings update symmetrically (zero-sum), with
a K-factor annealed from 40 → 10 over the first 30 attempts.

Pure functions; no data IO.
"""

from __future__ import annotations

from typing import Tuple

# Elo scale (FIDE convention): a 400-point gap → ~10× win-odds.
_ELO_SCALE = 400.0

# Annealing schedule for the per-attempt K-factor.
# Linear from attempt 0 (K_MAX) to attempt K_ANNEAL_OVER (K_MIN); held at
# K_MIN thereafter. Spec-defined (simulator v1 prompt).
_K_MAX = 40.0
_K_MIN = 10.0
_K_ANNEAL_OVER = 30


def expected(r_student: float, r_question: float) -> float:
    """Expected score for the student (in [0, 1]).

        E = 1 / (1 + 10 ** ((r_question - r_student) / 400))
    """
    return 1.0 / (1.0 + 10.0 ** ((r_question - r_student) / _ELO_SCALE))


def update(
    r_student: float,
    r_question: float,
    actual: bool,
    k: float,
) -> Tuple[float, float]:
    """Symmetric (zero-sum) Elo update.

    Returns (new_r_student, new_r_question). 'actual' is treated as 1.0
    for a correct response, 0.0 otherwise; the student's delta is
    K * (actual - E) and the question receives the opposite delta.
    """
    e = expected(r_student, r_question)
    delta = k * ((1.0 if actual else 0.0) - e)
    return r_student + delta, r_question - delta


def k_factor(attempts_so_far: int) -> float:
    """K-factor as a function of the student's attempt count.

    Linear anneal from K_MAX (attempt 0) to K_MIN (attempt K_ANNEAL_OVER),
    held at K_MIN thereafter. Negative counts are treated as 0.
    """
    if attempts_so_far <= 0:
        return _K_MAX
    if attempts_so_far >= _K_ANNEAL_OVER:
        return _K_MIN
    return _K_MAX - (_K_MAX - _K_MIN) * (attempts_so_far / _K_ANNEAL_OVER)
