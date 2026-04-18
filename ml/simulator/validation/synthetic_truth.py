"""Synthetic ground truth for self-consistency validation (Phase 1).

Generates a population of students + a pool of items with *known* 2PL
IRT discrimination/difficulty (a, b). Each student answers each item
once, outcome drawn from the 2PL model:

    outcome ~ Bernoulli( sigmoid( a_j · (theta_i − b_j) ) )

The resulting responses DataFrame matches the schema calibrators expect
(`user_id, problem_id, correct, skill_id`), so `fit_2pl` can recover
(a, b) and student θ from the synthetic responses.

**BKT is intentionally not modelled here.** Phase 1 tests the IRT half
of the stack; BKT recovery requires per-skill attempt *sequences* with
hidden-state transitions and slip/guess emissions, which in turn
requires real longitudinal student data (or a purpose-built BKT
generator). Both land in Phase 2. See docs/simulator/v1-validation.md §4.

Recovery of known params from a model's own draws is a necessary (not
sufficient) condition for the math to be right: if the simulator cannot
learn its own ground truth, it cannot possibly learn reality.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def _logistic(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


@dataclass(frozen=True)
class GroundTruth:
    theta_true: pd.DataFrame        # user_id, theta
    item_params: pd.DataFrame       # problem_id, a, b, skill_id
    responses: pd.DataFrame         # user_id, problem_id, correct, skill_id


def generate_ground_truth(
    n_students: int = 800,
    n_skills: int = 6,
    items_per_skill: int = 20,
    seed: int = 0,
) -> GroundTruth:
    """Draw students, items, and 2PL responses.

    - theta_i  ~ N(0, 1)
    - a_j      ~ Uniform(0.6, 2.0)        (discrimination)
    - b_j      ~ N(0, 1)                   (difficulty)
    - skill_id: items are partitioned equally across skills.
    - outcome  ~ Bernoulli( sigmoid( a_j · (theta_i − b_j) ) )
    """
    rng = np.random.default_rng(seed)

    users = np.arange(1, n_students + 1)
    theta = rng.normal(0.0, 1.0, size=n_students)

    n_items = n_skills * items_per_skill
    problem_ids = np.arange(1, n_items + 1)
    a = rng.uniform(0.6, 2.0, size=n_items)
    b = rng.normal(0.0, 1.0, size=n_items)
    skill_ids = np.repeat(np.arange(1, n_skills + 1), items_per_skill)

    # One response per (student, item). This is enough for IRT
    # (fit_2pl only needs the aggregate correct rate per (item,
    # student)); it is deliberately *not* enough for BKT, which needs
    # ordered attempt sequences per skill.
    rows = []
    theta_grid = theta[:, None]
    a_grid = a[None, :]
    b_grid = b[None, :]
    p = _logistic(a_grid * (theta_grid - b_grid))
    draws = rng.random((n_students, n_items)) < p
    for i, user_id in enumerate(users):
        for j, problem_id in enumerate(problem_ids):
            rows.append({
                "user_id": int(user_id),
                "problem_id": int(problem_id),
                "correct": bool(draws[i, j]),
                "skill_id": int(skill_ids[j]),
            })
    responses = pd.DataFrame(rows)

    theta_true = pd.DataFrame({"user_id": users, "theta": theta})
    item_params = pd.DataFrame({
        "problem_id": problem_ids,
        "a": a,
        "b": b,
        "skill_id": skill_ids,
    })

    return GroundTruth(
        theta_true=theta_true,
        item_params=item_params,
        responses=responses,
    )
