"""Self-consistency validation pipeline.

    synthetic ground truth   →   calibration   →   simulation   →   metrics

Stages:
    1. `generate_ground_truth` draws N_TRUTH students answering a known
       item pool, each item tagged with a known skill. Yields a
       `responses_df` in the calibrators' expected schema.
    2. `fit_2pl` + `fit_bkt` + `derive_priors` turn the raw responses
       into calibrated artefacts.
    3. A small `ItemBank` + `ConceptGraph` are built from the calibrated
       item params (one concept per skill, a linear prerequisite chain).
    4. `TermRunner` simulates `n_sim_students` across the term using the
       fitted params + priors, writing events through the PR 9 writer.
    5. `metrics` compares fitted vs true params and simulated vs truth
       distributions.

Returns a `ValidationReport` dict suitable for JSON dumping.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from ml.simulator.calibration.fit_2pl import fit_2pl
from ml.simulator.calibration.fit_bkt import fit_bkt
from ml.simulator.calibration.priors import derive_priors
from ml.simulator.config import SimulationConfig
from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.io.local_writer import LocalParquetWriter
from ml.simulator.loop.runner import TermRunner
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.profile import AttemptRecord, StudentProfile
from ml.simulator.validation import metrics
from ml.simulator.validation.synthetic_truth import GroundTruth, generate_ground_truth


@dataclass
class ValidationReport:
    seed: int
    n_truth_students: int
    n_items: int
    n_skills: int
    n_sim_students: int
    fit_2pl_converged: bool
    recovery_2pl: dict
    recovery_theta: dict
    recovery_bkt: dict
    truth_correct_rate_summary: dict
    sim_correct_rate_summary: dict
    correct_rate_ks: dict
    response_time_fit: dict
    learning_curve: dict

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "n_truth_students": self.n_truth_students,
            "n_items": self.n_items,
            "n_skills": self.n_skills,
            "n_sim_students": self.n_sim_students,
            "fit_2pl_converged": self.fit_2pl_converged,
            "recovery_2pl": self.recovery_2pl,
            "recovery_theta": self.recovery_theta,
            "recovery_bkt": self.recovery_bkt,
            "truth_correct_rate_summary": self.truth_correct_rate_summary,
            "sim_correct_rate_summary": self.sim_correct_rate_summary,
            "correct_rate_ks": self.correct_rate_ks,
            "response_time_fit": self.response_time_fit,
            "learning_curve": self.learning_curve,
        }


def _build_concept_graph_from_skills(skill_ids: list[int]) -> ConceptGraph:
    """Linear prerequisite chain: skill_1 → skill_2 → … so the
    TermRunner's topological_next advances across the chain.
    """
    g = nx.DiGraph()
    ordered = sorted(skill_ids)
    g.add_nodes_from(ordered)
    for src, dst in zip(ordered, ordered[1:]):
        g.add_edge(src, dst)
    return ConceptGraph(g)


def _build_item_bank(fitted_items: pd.DataFrame, skill_map: dict[int, int]) -> ItemBank:
    items: list[Item] = []
    for row in fitted_items.itertuples(index=False):
        concept_id = skill_map.get(int(row.item_id))
        if concept_id is None:
            continue
        items.append(Item(
            item_id=int(row.item_id),
            concept_id=int(concept_id),
            a=float(row.a),
            b=float(row.b),
        ))
    return ItemBank(items)


def _bkt_params_by_concept(fitted_bkt: pd.DataFrame) -> dict[int, BKTParams]:
    out: dict[int, BKTParams] = {}
    for row in fitted_bkt.itertuples(index=False):
        out[int(row.skill_id)] = BKTParams(
            p_init=float(row.p_init),
            p_transit=float(row.p_transit),
            p_slip=float(row.p_slip),
            p_guess=float(row.p_guess),
        )
    return out


def _build_student(
    student_id: int,
    priors: dict,
    concepts: list[int],
    rng: np.random.Generator,
) -> StudentProfile:
    theta_mean = priors.get("theta_mean", 0.0)
    theta_std = priors.get("theta_std", 1.0)
    base = float(rng.normal(theta_mean, theta_std))
    slip_mean = priors.get("slip_prior", {}).get("mean", 0.1)
    guess_mean = priors.get("guess_prior", {}).get("mean", 0.25)
    lr_mu = priors.get("learning_rate_lognorm", {}).get("mu", math.log(0.15))
    lr_sigma = priors.get("learning_rate_lognorm", {}).get("sigma", 0.3)
    rt_mu = (priors.get("response_time_lognorm") or {}).get("mu", math.log(8000.0))
    rt_sigma = (priors.get("response_time_lognorm") or {}).get("sigma", 0.3)

    learning_rate = float(math.exp(rng.normal(lr_mu, lr_sigma)))
    return StudentProfile(
        student_id=student_id,
        true_theta={c: base + float(rng.normal(0.0, 0.2)) for c in concepts},
        estimated_theta={c: (0.0, 1.0) for c in concepts},
        bkt_state={c: BKTState(p_known=0.2) for c in concepts},
        elo_rating=1200.0,
        recall_half_life={c: 24.0 for c in concepts},
        last_retrieval={},
        learning_rate=learning_rate,
        slip=float(slip_mean),
        guess=float(guess_mean),
        engagement_decay=0.95,
        response_time_lognorm_params=(float(rt_mu), float(rt_sigma)),
        attempts_history=[],
    )


def run_validation(
    n_truth_students: int = 400,
    n_skills: int = 4,
    items_per_skill: int = 12,
    n_sim_students: int = 200,
    n_sessions: int = 15,
    seed: int = 42,
    parquet_output_dir: str | Path | None = None,
    run_id: str = "validation",
) -> ValidationReport:
    # Stage 1: synthetic ground truth.
    truth: GroundTruth = generate_ground_truth(
        n_students=n_truth_students,
        n_skills=n_skills,
        items_per_skill=items_per_skill,
        seed=seed,
    )

    # Stage 2: calibrate on the truth's responses.
    fit2pl = fit_2pl(truth.responses, seed=seed)
    fitted_bkt = fit_bkt(truth.responses)
    priors = derive_priors(
        theta_estimates=fit2pl.theta_estimates,
        bkt_params=fitted_bkt,
        responses_df=truth.responses,
    )

    # Stage 3: build the simulator's world from the fitted artefacts.
    skill_map = dict(zip(
        truth.item_params["problem_id"].astype(int),
        truth.item_params["skill_id"].astype(int),
    ))
    bank = _build_item_bank(fit2pl.item_params, skill_map)
    concepts = sorted(set(skill_map.values()))
    graph = _build_concept_graph_from_skills(concepts)
    bkt_by_concept = _bkt_params_by_concept(fitted_bkt)

    # Stage 4: simulate a fresh cohort.
    master_rng = np.random.default_rng(seed + 1)
    start_time = datetime(2024, 1, 1, 9, 0, 0)
    sim_config = SimulationConfig(
        n_students=n_sim_students, term_weeks=n_sessions // 3 or 1,
        sessions_per_week=3, minutes_per_session=20,
        subject="math", seed=seed,
    )

    all_attempts: list[AttemptRecord] = []
    writer_ctx = (
        LocalParquetWriter(parquet_output_dir, run_id, sim_config)
        if parquet_output_dir is not None
        else None
    )
    try:
        for i in range(n_sim_students):
            student_seed = int(master_rng.integers(0, 2**31 - 1))
            student_rng = np.random.default_rng(student_seed)
            profile = _build_student(
                student_id=i, priors=priors, concepts=concepts, rng=student_rng,
            )
            runner = TermRunner(
                student=profile,
                concept_graph=graph,
                item_bank=bank,
                bkt_params_by_concept=bkt_by_concept,
                start_time=start_time,
                n_sessions=n_sessions,
                session_interval_hours=24.0,
                quiz_items_per_session=5,
                revise_items_per_concept=1,
                seed=student_seed,
            )
            for event in runner.run():
                if writer_ctx is not None:
                    writer_ctx.write(event)
                if isinstance(event, AttemptRecord):
                    all_attempts.append(event)
    finally:
        if writer_ctx is not None:
            writer_ctx.close()

    sim_attempts_df = pd.DataFrame([
        {
            "concept_id": a.concept_id,
            "item_id": a.item_id,
            "is_correct": bool(a.is_correct),
            "response_time_ms": a.response_time_ms,
        }
        for a in all_attempts
    ])

    # Stage 5: metrics.
    truth_per_user = (
        truth.responses.groupby("user_id")["correct"].mean().to_numpy()
    )
    if len(sim_attempts_df):
        # Synthesise a per-student correct rate from the parquet-equivalent data.
        # We grouped events without student_id above; rebuild by running again
        # would be wasteful. Instead bucket every `k` attempts as one student.
        rates = []
        attempts_per_student = max(1, len(all_attempts) // max(1, n_sim_students))
        for i in range(n_sim_students):
            slice_ = all_attempts[i * attempts_per_student : (i + 1) * attempts_per_student]
            if slice_:
                rates.append(np.mean([a.is_correct for a in slice_]))
        sim_per_user = np.array(rates) if rates else np.array([0.0])
    else:
        sim_per_user = np.array([0.0])

    recovery_2pl_ = metrics.recovery_2pl(
        truth.item_params.rename(columns={}),  # already problem_id, a, b
        fit2pl.item_params,
    )
    recovery_theta_ = metrics.recovery_theta(truth.theta_true, fit2pl.theta_estimates)
    recovery_bkt_ = metrics.recovery_bkt(truth.bkt_params, fitted_bkt)
    ks = metrics.ks_correct_rate(sim_per_user, truth_per_user)
    rt_fit = metrics.response_time_fit(
        sim_attempts_df["response_time_ms"].to_numpy() if len(sim_attempts_df) else np.array([0])
    )
    curve = metrics.learning_curve_slope(sim_attempts_df)

    def _summary(arr: np.ndarray) -> dict:
        return {
            "n": int(len(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "p10": float(np.percentile(arr, 10)),
            "p90": float(np.percentile(arr, 90)),
        }

    return ValidationReport(
        seed=seed,
        n_truth_students=n_truth_students,
        n_items=len(truth.item_params),
        n_skills=n_skills,
        n_sim_students=n_sim_students,
        fit_2pl_converged=fit2pl.converged,
        recovery_2pl=recovery_2pl_,
        recovery_theta=recovery_theta_,
        recovery_bkt=recovery_bkt_,
        truth_correct_rate_summary=_summary(truth_per_user),
        sim_correct_rate_summary=_summary(sim_per_user),
        correct_rate_ks=ks,
        response_time_fit=rt_fit,
        learning_curve=curve,
    )
