"""Synthetic ground truth for self-consistency validation.

Generates a population of students + a pool of items with *known* 2PL
IRT discrimination/difficulty (a, b) and *known* BKT params per skill.
Each student answers each item once, outcome drawn from the 2PL model.

The resulting responses DataFrame matches the schema calibrators expect
(`user_id, problem_id, correct, skill_id`), so the full calibration
pipeline can recover these params from the synthetic responses.

Recovery of known params from a model's own draws is a necessary
(not sufficient) condition for the math to be right: if the simulator
cannot learn its own ground truth, it cannot possibly learn reality.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def _logistic(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


@dataclass(frozen=True)
class GroundTruth:
    theta_true: pd.DataFrame        # user_id, theta
    item_params: pd.DataFrame       # problem_id, a, b, skill_id
    bkt_params: pd.DataFrame        # skill_id, p_init, p_transit, p_slip, p_guess
    responses: pd.DataFrame         # user_id, problem_id, correct, skill_id


def generate_ground_truth(
    n_students: int = 800,
    n_skills: int = 6,
    items_per_skill: int = 20,
    seed: int = 0,
) -> GroundTruth:
    """Draw students, items, and responses under known 2PL + BKT params.

    - theta_i  ~ N(0, 1)
    - a_j      ~ Uniform(0.6, 2.0)        (discrimination)
    - b_j      ~ N(0, 1)                   (difficulty)
    - skill_id: items are partitioned equally across skills.
    - outcome  ~ Bernoulli( 2PL(theta, a, b) )
    """
    rng = np.random.default_rng(seed)

    users = np.arange(1, n_students + 1)
    theta = rng.normal(0.0, 1.0, size=n_students)

    n_items = n_skills * items_per_skill
    problem_ids = np.arange(1, n_items + 1)
    a = rng.uniform(0.6, 2.0, size=n_items)
    b = rng.normal(0.0, 1.0, size=n_items)
    skill_ids = np.repeat(np.arange(1, n_skills + 1), items_per_skill)

    # Known BKT params per skill. Chosen wide enough that the EM fit
    # has room to move without crossing the Beck-Chang boundary.
    bkt_rows = []
    for s in range(1, n_skills + 1):
        bkt_rows.append({
            "skill_id": s,
            "p_init": float(rng.uniform(0.10, 0.30)),
            "p_transit": float(rng.uniform(0.10, 0.25)),
            "p_slip": float(rng.uniform(0.05, 0.15)),
            "p_guess": float(rng.uniform(0.15, 0.30)),
        })
    bkt_params = pd.DataFrame(bkt_rows)

    # Draw responses: each student answers each item once. For the IRT
    # fit we don't need the BKT-ordered longitudinal structure — the
    # calibration test is that fit_2pl recovers (a, b) and fit_bkt
    # recovers the per-skill BKT params from the observed correct rates.
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
        bkt_params=bkt_params,
        responses=responses,
    )
