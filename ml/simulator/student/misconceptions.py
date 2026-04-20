"""Phase 2 PR B1 — student misconception susceptibility.

Populates the `misconception_susceptibility: dict[int, float]` field on
`StudentProfile` (reserved empty in Phase 1 per `profile.py` docstring).
The field is a sparse map *misconception_id → weight in [0, 1]*, where
the weight is the propensity of this student to endorse the distractor
encoding that misconception given the chance. Keys are the integer
misconception IDs from the Eedi 2024 catalogue (the catalogue ships
int IDs directly — the concern-list concept-id-scheme mismatch is
resolved by keeping the Eedi ID as-is and committing an explicit
int-mapping file for traceability; see `build_eedi_id_map.py`).

Distributional design
---------------------

Per student we draw two knobs:

1. **Activity rate** `r` in `[0, 1]` — the fraction of the catalogue
   for which the student has non-zero susceptibility. Drawn from a
   Beta distribution whose mean is tied to the student's scalar
   ability θ:

       mean_r(θ) = clip( _BASE_RATE + _THETA_COEF * (_THETA_NEUTRAL - θ),
                         _MIN_MEAN_RATE, _MAX_MEAN_RATE )

   Higher-θ students → lower mean activity. The Beta concentration
   parameter is fixed via `_BETA_NU`, so each student's `r` spreads
   around the mean within [0, 1].

2. **Per-misconception weights** — for each active misconception
   (chosen by a Bernoulli(r) independently per ID), a weight is drawn
   from `Uniform(_WEIGHT_MIN, _WEIGHT_MAX)`. Non-active
   misconceptions are absent from the dict (the sparsity contract).

This matches the concern-list note that B1 must assign heterogeneous
susceptibilities: `r` varies across students (ability-correlated),
and the active-set identity varies across students (Bernoulli draws
with independent RNG streams).

Constants live here, not in `config.py`, because they parameterise
the sampler's distribution shape and the distribution shape is part
of the simulator's published interface — changing them is a new
simulator version, not a runtime knob.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

# Scalar θ neutral point — on the standard 2PL scale θ=0 is the cohort mean.
_THETA_NEUTRAL = 0.0
# Slope of the mean-activity-rate vs. θ relationship. At θ=-1 the mean
# activity rate climbs by +0.08 above the base; at θ=+1 it drops by the
# same. Choice is pedagogical: lower ability correlates with more
# misconceptions being live (per Ashlock 2010 "Error Patterns in
# Computation"). Magnitude chosen so (θ ∈ [-2, 2]) keeps the mean rate
# inside `[_MIN_MEAN_RATE, _MAX_MEAN_RATE]`.
_THETA_COEF = 0.08
# Base activity rate at θ=0 (the cohort mean student).
_BASE_RATE = 0.12
# Floor / ceiling on the Beta mean so the sampler never produces a
# trivially empty or near-saturated susceptibility map even in the
# tails of the θ prior.
_MIN_MEAN_RATE = 0.02
_MAX_MEAN_RATE = 0.35
# Beta concentration ν = α + β. Lower ν = wider spread of per-student
# r around the mean. 8 is moderate: a θ=0 student with mean rate 0.12
# has 90% CI roughly [0.03, 0.27].
_BETA_NU = 8.0
# Per-misconception weight range once active. Endpoints chosen so that
# an "active" misconception is meaningfully non-zero (0.2 floor) but
# never dominating (0.9 ceiling); B2's response model multiplies these
# into the logit, so 1.0 would let one misconception outvote IRT.
_WEIGHT_MIN = 0.20
_WEIGHT_MAX = 0.90


@dataclass(frozen=True)
class SusceptibilityConfig:
    """Tunable knobs (all with module-level defaults)."""

    theta_neutral: float = _THETA_NEUTRAL
    theta_coef: float = _THETA_COEF
    base_rate: float = _BASE_RATE
    min_mean_rate: float = _MIN_MEAN_RATE
    max_mean_rate: float = _MAX_MEAN_RATE
    beta_nu: float = _BETA_NU
    weight_min: float = _WEIGHT_MIN
    weight_max: float = _WEIGHT_MAX


def _mean_rate(theta: float, cfg: SusceptibilityConfig) -> float:
    raw = cfg.base_rate + cfg.theta_coef * (cfg.theta_neutral - theta)
    return float(np.clip(raw, cfg.min_mean_rate, cfg.max_mean_rate))


def _beta_params(mean: float, nu: float) -> tuple[float, float]:
    """Convert (mean, concentration) → (alpha, beta) for scipy/numpy."""
    alpha = mean * nu
    beta = (1.0 - mean) * nu
    # Guard against degenerate (alpha <= 0 or beta <= 0) from boundary means.
    alpha = max(alpha, 1e-3)
    beta = max(beta, 1e-3)
    return alpha, beta


@dataclass
class SusceptibilitySampler:
    """Produces per-student `misconception_susceptibility` dicts.

    The sampler is stateless across students — determinism comes from
    the caller threading a `np.random.Generator` seeded per student.
    """

    misconception_ids: np.ndarray  # 1-D int array; canonical catalogue order
    config: SusceptibilityConfig = field(default_factory=SusceptibilityConfig)

    def __post_init__(self) -> None:
        self.misconception_ids = np.asarray(self.misconception_ids, dtype=np.int64)
        if self.misconception_ids.ndim != 1:
            raise ValueError("misconception_ids must be 1-D")
        if len(self.misconception_ids) == 0:
            raise ValueError("misconception_ids is empty; need a non-empty catalogue")
        if len(np.unique(self.misconception_ids)) != len(self.misconception_ids):
            raise ValueError("misconception_ids contains duplicates")

    def draw(
        self, theta_scalar: float, rng: np.random.Generator
    ) -> dict[int, float]:
        """Return a sparse {misconception_id: weight_in_[weight_min, weight_max]} map."""
        cfg = self.config
        mean_r = _mean_rate(theta_scalar, cfg)
        alpha, beta = _beta_params(mean_r, cfg.beta_nu)
        r = float(rng.beta(alpha, beta))
        n = len(self.misconception_ids)
        active_mask = rng.random(n) < r
        if not active_mask.any():
            return {}
        active_ids = self.misconception_ids[active_mask]
        weights = rng.uniform(cfg.weight_min, cfg.weight_max, size=active_ids.shape[0])
        return {int(mid): float(w) for mid, w in zip(active_ids, weights)}


def scalar_theta_from_profile_thetas(per_concept_theta: Iterable[float]) -> float:
    """Reduce per-concept θ dict values to one scalar for susceptibility.

    The sampler is cheap and should not re-draw ability; the student
    generator already picked `base ~ N(theta_mean, theta_std)`. We
    approximate that scalar post-hoc as the mean over concept thetas,
    which matches Phase 1's scalar-ability summary.
    """
    vals = list(per_concept_theta)
    if not vals:
        return 0.0
    return float(np.mean(vals))
