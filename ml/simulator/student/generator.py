"""Draws synthetic students from calibrated priors.

The generator consumes:

    * `priors`              — the JSON emitted by
      `ml.simulator.calibration.priors.derive_priors` (theta mean/std,
      slip/guess priors, learning-rate log-normal, response-time log-normal).
    * `concept_graph`       — `ConceptGraph` from PR 6; determines the
      concept universe and the prerequisite ordering used for correlated
      theta draws.
    * `bkt_params_by_concept` — per-concept `BKTParams` from `fit_bkt`;
      falls back to a sensible default when a concept is missing.

Cross-concept `true_theta` is correlated along graph edges with
coefficient ρ (default 0.6, per spec). We walk the graph in topological
order, so a child concept's theta is drawn conditional on the mean of
its parent concepts:

    θ_c | θ_parents ~ N(ρ · mean(θ_parents) + (1 − ρ) · base, √(1 − ρ²))

where `base` is the student-global latent ability drawn from the
`theta_mean` / `theta_std` prior. Concepts without prerequisites draw
straight from `N(base, √(1 − ρ²))`. All thetas are clamped to
`[-4, 4]` to match the IRT calibrator bounds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.profile import StudentProfile

# Correlation between a concept's true theta and the mean of its direct
# prerequisites. 0.6 per the v1 spec — tight enough that prerequisites
# matter, loose enough that individual concepts still carry signal.
_THETA_CORRELATION = 0.6
# Starting half-life applied uniformly at generation time (hours).
# The loop overwrites this per concept as practice happens.
_DEFAULT_HALF_LIFE_HOURS = 24.0
# Starting Elo rating. FIDE convention uses 1200 for a "new" player.
_INITIAL_ELO = 1200.0
# Fallback BKT defaults when a concept was not in the calibrated set.
_DEFAULT_BKT = BKTParams(p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25)
# Fallback response-time log-normal (~10 s ±).
_DEFAULT_RT_MU = math.log(10_000.0)
_DEFAULT_RT_SIGMA = 0.5
# Bounds on theta draws, matching fit_2pl.
_THETA_LOWER = -4.0
_THETA_UPPER = 4.0


@dataclass
class StudentGenerator:
    priors: dict
    concept_graph: ConceptGraph
    bkt_params_by_concept: dict[int, BKTParams] = field(default_factory=dict)
    correlation: float = _THETA_CORRELATION
    default_half_life_hours: float = _DEFAULT_HALF_LIFE_HOURS
    initial_elo: float = _INITIAL_ELO

    def draw(self, student_id: int, rng: np.random.Generator) -> StudentProfile:
        theta_mean = float(self.priors.get("theta_mean", 0.0))
        theta_std = max(float(self.priors.get("theta_std", 1.0)), 1e-6)
        base = float(rng.normal(theta_mean, theta_std))

        learning_rate = self._draw_learning_rate(rng)
        slip, guess = self._draw_slip_guess(rng)
        rt_params = self._draw_response_time_params()

        true_theta = self._draw_true_theta(base, rng)
        bkt_state = {
            c: BKTState(p_known=self._bkt_for(c).p_init) for c in true_theta
        }
        recall_half_life = {c: self.default_half_life_hours for c in true_theta}
        last_retrieval: dict = {}

        return StudentProfile(
            student_id=student_id,
            true_theta=true_theta,
            estimated_theta={c: (0.0, 1.0) for c in true_theta},
            bkt_state=bkt_state,
            elo_rating=self.initial_elo,
            recall_half_life=recall_half_life,
            last_retrieval=last_retrieval,
            learning_rate=learning_rate,
            slip=slip,
            guess=guess,
            engagement_decay=0.95,
            response_time_lognorm_params=rt_params,
            attempts_history=[],
            misconception_susceptibility={},
        )

    def _bkt_for(self, concept_id: int) -> BKTParams:
        return self.bkt_params_by_concept.get(concept_id, _DEFAULT_BKT)

    def _draw_learning_rate(self, rng: np.random.Generator) -> float:
        lr = self.priors.get("learning_rate_lognorm") or {}
        mu = float(lr.get("mu", math.log(0.1)))
        sigma = max(float(lr.get("sigma", 0.0)), 0.0)
        return float(np.exp(rng.normal(mu, sigma) if sigma > 0.0 else mu))

    def _draw_slip_guess(self, rng: np.random.Generator) -> tuple[float, float]:
        slip_p = self.priors.get("slip_prior") or {"mean": 0.1, "std": 0.0}
        guess_p = self.priors.get("guess_prior") or {"mean": 0.25, "std": 0.0}
        slip_std = max(float(slip_p.get("std", 0.0)), 0.0)
        guess_std = max(float(guess_p.get("std", 0.0)), 0.0)
        slip = float(np.clip(
            rng.normal(slip_p["mean"], slip_std) if slip_std > 0 else slip_p["mean"],
            0.0, 0.5,
        ))
        guess = float(np.clip(
            rng.normal(guess_p["mean"], guess_std) if guess_std > 0 else guess_p["mean"],
            0.0, 0.5,
        ))
        return slip, guess

    def _draw_response_time_params(self) -> tuple[float, float]:
        rt = self.priors.get("response_time_lognorm")
        if rt is None:
            return (_DEFAULT_RT_MU, _DEFAULT_RT_SIGMA)
        return (float(rt.get("mu", _DEFAULT_RT_MU)), float(rt.get("sigma", _DEFAULT_RT_SIGMA)))

    def _draw_true_theta(
        self, base: float, rng: np.random.Generator
    ) -> dict[int, float]:
        rho = self.correlation
        noise_sigma = math.sqrt(max(1.0 - rho * rho, 0.0))
        true_theta: dict[int, float] = {}
        for concept in nx.topological_sort(self.concept_graph.graph):
            prereqs = self.concept_graph.prerequisites(concept)
            if not prereqs:
                t = base + float(rng.normal(0.0, noise_sigma))
            else:
                parent_mean = float(
                    np.mean([true_theta[p] for p in prereqs])
                )
                mean = rho * parent_mean + (1.0 - rho) * base
                t = mean + float(rng.normal(0.0, noise_sigma))
            true_theta[concept] = float(np.clip(t, _THETA_LOWER, _THETA_UPPER))
        return true_theta
