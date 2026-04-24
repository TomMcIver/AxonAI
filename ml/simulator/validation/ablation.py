"""Phase 2 PR B12 — ablation study.

Measures the marginal contribution of each Gate B feature by running the
B11 pipeline with one feature disabled at a time and comparing metrics
against the full-system baseline.

Ablation conditions
-------------------

| Condition           | What is disabled                                      |
|---------------------|-------------------------------------------------------|
| full                | Nothing — the B11 baseline                           |
| no_susceptibility   | B1: all students have empty misconception_susceptibility |
| no_detector         | B5: MisconceptionDetector removed → Rule 1 never fires |
| default_style_only  | B6: style selector always returns concise_answer      |
| no_slow_students    | B7 trigger: no slow-response students → analogy never fires |

For each condition the same synthetic cohort and item bank are used
(same seed), so differences are attributable to the ablated feature.

Metrics reported per condition
-------------------------------

- `style_distribution`: dict[str, int] — how often each style fires
- `contrast_with_misconception_rate`: float — fraction of attempts using Rule 1
- `bkt_growth`: float — mean final p_known − mean initial p_known
- `mean_correct_rate`: float — fraction of correct attempts overall

`AblationReport.delta` computes the per-metric difference from the
baseline for a given condition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import ItemBank
from ml.simulator.loop.explanation_style import (
    CONCISE_ANSWER,
    CONTRAST_WITH_MISCONCEPTION,
    ExplanationStyleConfig,
    STYLES,
)
from ml.simulator.loop.runner import TermRunner
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.misconceptions import SusceptibilitySampler
from ml.simulator.student.profile import AttemptRecord, StudentProfile
from ml.simulator.validation.phase2_pipeline import (
    _build_bkt_params,
    _build_concept_graph,
    _build_synthetic_bank,
)

# ---------------------------------------------------------------------------
# Condition names
# ---------------------------------------------------------------------------

CONDITION_FULL = "full"
CONDITION_NO_SUSCEPTIBILITY = "no_susceptibility"
CONDITION_NO_DETECTOR = "no_detector"
CONDITION_DEFAULT_STYLE_ONLY = "default_style_only"
CONDITION_NO_SLOW_STUDENTS = "no_slow_students"

ALL_CONDITIONS = [
    CONDITION_FULL,
    CONDITION_NO_SUSCEPTIBILITY,
    CONDITION_NO_DETECTOR,
    CONDITION_DEFAULT_STYLE_ONLY,
    CONDITION_NO_SLOW_STUDENTS,
]

# ---------------------------------------------------------------------------
# Per-condition metrics
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConditionMetrics:
    condition: str
    n_attempts: int
    style_distribution: dict[str, int]
    contrast_with_misconception_rate: float
    bkt_growth: float
    mean_correct_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "n_attempts": self.n_attempts,
            "style_distribution": self.style_distribution,
            "contrast_with_misconception_rate": self.contrast_with_misconception_rate,
            "bkt_growth": self.bkt_growth,
            "mean_correct_rate": self.mean_correct_rate,
        }


@dataclass(frozen=True)
class AblationReport:
    """Results of all ablation conditions."""

    conditions: tuple[ConditionMetrics, ...]
    baseline_condition: str = CONDITION_FULL

    def get(self, condition: str) -> ConditionMetrics | None:
        for c in self.conditions:
            if c.condition == condition:
                return c
        return None

    def delta(self, condition: str, metric: str) -> float | None:
        """Return (condition metric) − (baseline metric), or None if missing."""
        base = self.get(self.baseline_condition)
        cond = self.get(condition)
        if base is None or cond is None:
            return None
        return getattr(cond, metric) - getattr(base, metric)

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_condition": self.baseline_condition,
            "conditions": [c.to_dict() for c in self.conditions],
        }


# ---------------------------------------------------------------------------
# Profile builders for each condition
# ---------------------------------------------------------------------------

def _build_profiles_full(
    n_students: int, n_concepts: int, seed: int, slow_fraction: float = 0.10
) -> list[StudentProfile]:
    rng = np.random.default_rng(seed)
    misc_ids = np.array(
        [c * 100 + r for c in range(1, n_concepts + 1) for r in range(5)],
        dtype=np.int64,
    )
    sampler = SusceptibilitySampler(misconception_ids=misc_ids)
    n_slow = max(1, int(n_students * slow_fraction))
    profiles: list[StudentProfile] = []
    for sid in range(n_students):
        theta = {c: float(rng.normal(0.0, 1.0)) for c in range(1, n_concepts + 1)}
        scalar_theta = float(np.mean(list(theta.values())))
        susceptibility = sampler.draw(scalar_theta, rng)
        rt_params = (
            (math.log(35000), 0.3) if sid < n_slow else (math.log(8000), 0.4)
        )
        profiles.append(StudentProfile(
            student_id=sid,
            true_theta=theta,
            estimated_theta={c: (v, 1.0) for c, v in theta.items()},
            bkt_state={c: BKTState(p_known=0.2) for c in range(1, n_concepts + 1)},
            elo_rating=1200.0,
            recall_half_life={c: 24.0 for c in range(1, n_concepts + 1)},
            last_retrieval={},
            learning_rate=0.1,
            slip=0.1,
            guess=0.25,
            engagement_decay=0.95,
            response_time_lognorm_params=rt_params,
            misconception_susceptibility=susceptibility,
        ))
    return profiles


def _build_profiles_no_susceptibility(
    n_students: int, n_concepts: int, seed: int
) -> list[StudentProfile]:
    """B1 ablation: all students have empty susceptibility."""
    rng = np.random.default_rng(seed)
    profiles: list[StudentProfile] = []
    for sid in range(n_students):
        theta = {c: float(rng.normal(0.0, 1.0)) for c in range(1, n_concepts + 1)}
        profiles.append(StudentProfile(
            student_id=sid,
            true_theta=theta,
            estimated_theta={c: (v, 1.0) for c, v in theta.items()},
            bkt_state={c: BKTState(p_known=0.2) for c in range(1, n_concepts + 1)},
            elo_rating=1200.0,
            recall_half_life={c: 24.0 for c in range(1, n_concepts + 1)},
            last_retrieval={},
            learning_rate=0.1,
            slip=0.1,
            guess=0.25,
            engagement_decay=0.95,
            response_time_lognorm_params=(math.log(8000), 0.4),
            misconception_susceptibility={},  # B1 ablated
        ))
    return profiles


def _build_profiles_no_slow(
    n_students: int, n_concepts: int, seed: int
) -> list[StudentProfile]:
    """No slow-response students → analogy style never fires."""
    rng = np.random.default_rng(seed)
    misc_ids = np.array(
        [c * 100 + r for c in range(1, n_concepts + 1) for r in range(5)],
        dtype=np.int64,
    )
    sampler = SusceptibilitySampler(misconception_ids=misc_ids)
    profiles: list[StudentProfile] = []
    for sid in range(n_students):
        theta = {c: float(rng.normal(0.0, 1.0)) for c in range(1, n_concepts + 1)}
        scalar_theta = float(np.mean(list(theta.values())))
        susceptibility = sampler.draw(scalar_theta, rng)
        profiles.append(StudentProfile(
            student_id=sid,
            true_theta=theta,
            estimated_theta={c: (v, 1.0) for c, v in theta.items()},
            bkt_state={c: BKTState(p_known=0.2) for c in range(1, n_concepts + 1)},
            elo_rating=1200.0,
            recall_half_life={c: 24.0 for c in range(1, n_concepts + 1)},
            last_retrieval={},
            learning_rate=0.1,
            slip=0.1,
            guess=0.25,
            engagement_decay=0.95,
            response_time_lognorm_params=(math.log(8000), 0.4),  # all fast
            misconception_susceptibility=susceptibility,
        ))
    return profiles


# ---------------------------------------------------------------------------
# Run one condition
# ---------------------------------------------------------------------------

def _run_condition(
    condition: str,
    profiles: list[StudentProfile],
    bank: ItemBank,
    concept_graph: ConceptGraph,
    bkt_params: dict[int, BKTParams],
    n_sessions: int,
    seed: int,
) -> ConditionMetrics:
    use_detector = condition not in (CONDITION_NO_DETECTOR, CONDITION_NO_SUSCEPTIBILITY)
    detector = MisconceptionDetector() if use_detector else None

    style_config: ExplanationStyleConfig | None = None
    if condition == CONDITION_DEFAULT_STYLE_ONLY:
        from ml.simulator.loop.explanation_style import ExplanationStyleConfig
        # Force all thresholds to impossible values so only Rule 5 fires.
        style_config = ExplanationStyleConfig(
            misconception_confidence_threshold=2.0,  # > 1 → never
            not_learned_threshold=0.0,               # < 0 → never
            streak_wrong_threshold=10_000,           # huge → never
            slow_response_ms=10_000_000,             # 10k s → never
        )

    start_time = datetime(2024, 1, 1)
    all_attempts: list[AttemptRecord] = []
    initial_bkt: list[float] = []
    final_bkt: list[float] = []

    for profile in profiles:
        initial_bkt.append(
            float(np.mean([s.p_known for s in profile.bkt_state.values()]))
        )
        runner = TermRunner(
            student=profile,
            concept_graph=concept_graph,
            item_bank=bank,
            bkt_params_by_concept=bkt_params,
            start_time=start_time,
            n_sessions=n_sessions,
            seed=seed,
            misconception_detector=detector,
            explanation_style_config=style_config,
        )
        for event in runner.run():
            if isinstance(event, AttemptRecord):
                all_attempts.append(event)
        final_bkt.append(
            float(np.mean([s.p_known for s in runner.final_profile.bkt_state.values()]))
        )

    style_dist = {s: 0 for s in STYLES}
    for a in all_attempts:
        if a.explanation_style in style_dist:
            style_dist[a.explanation_style] += 1

    n = len(all_attempts)
    cwm_rate = style_dist.get(CONTRAST_WITH_MISCONCEPTION, 0) / n if n > 0 else 0.0
    correct_rate = sum(a.is_correct for a in all_attempts) / n if n > 0 else 0.0
    bkt_growth = (
        float(np.mean(final_bkt)) - float(np.mean(initial_bkt))
        if initial_bkt else 0.0
    )

    return ConditionMetrics(
        condition=condition,
        n_attempts=n,
        style_distribution=style_dist,
        contrast_with_misconception_rate=cwm_rate,
        bkt_growth=bkt_growth,
        mean_correct_rate=correct_rate,
    )


# ---------------------------------------------------------------------------
# Main ablation entry point
# ---------------------------------------------------------------------------

def run_ablation_study(
    n_students: int = 80,
    n_sessions: int = 8,
    n_concepts: int = 3,
    n_items_per_concept: int = 4,
    seed: int = 42,
    conditions: list[str] | None = None,
) -> AblationReport:
    """Run all ablation conditions and return an `AblationReport`.

    Parameters
    ----------
    conditions:
        Subset of `ALL_CONDITIONS` to run. Defaults to all five.
    """
    if conditions is None:
        conditions = list(ALL_CONDITIONS)

    bank = _build_synthetic_bank(n_concepts, n_items_per_concept, seed)
    concept_graph = _build_concept_graph(n_concepts)
    bkt_params = _build_bkt_params(n_concepts)

    # Build profiles for each distinct condition type.
    profiles_full = _build_profiles_full(n_students, n_concepts, seed)
    profiles_no_susc = _build_profiles_no_susceptibility(n_students, n_concepts, seed)
    profiles_no_slow = _build_profiles_no_slow(n_students, n_concepts, seed)

    _profiles_map = {
        CONDITION_FULL: profiles_full,
        CONDITION_NO_SUSCEPTIBILITY: profiles_no_susc,
        CONDITION_NO_DETECTOR: profiles_full,       # same profiles, detector off
        CONDITION_DEFAULT_STYLE_ONLY: profiles_full, # same profiles, style locked
        CONDITION_NO_SLOW_STUDENTS: profiles_no_slow,
    }

    results: list[ConditionMetrics] = []
    for cond in conditions:
        profiles = _profiles_map[cond]
        metrics = _run_condition(
            cond, profiles, bank, concept_graph, bkt_params, n_sessions, seed
        )
        results.append(metrics)

    return AblationReport(conditions=tuple(results))


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_ablation_report(report: AblationReport, out_path: str) -> None:
    """Write a human-readable markdown ablation report."""
    from pathlib import Path
    import json

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    base = report.get(report.baseline_condition)
    lines = [
        "# Phase 2 PR B12 — Ablation Study Report",
        "",
        f"**Generated:** {datetime.utcnow().isoformat()}Z",
        f"**Baseline:** `{report.baseline_condition}`",
        "",
        "## Per-condition metrics",
        "",
        "| Condition | n_attempts | cwm_rate | bkt_growth | correct_rate |",
        "|-----------|-----------|----------|------------|--------------|",
    ]
    for c in report.conditions:
        lines.append(
            f"| `{c.condition}` | {c.n_attempts} | "
            f"{c.contrast_with_misconception_rate:.3f} | "
            f"{c.bkt_growth:+.4f} | "
            f"{c.mean_correct_rate:.3f} |"
        )

    if base is not None:
        lines += [
            "",
            "## Delta from baseline (condition − full)",
            "",
            "| Condition | Δ cwm_rate | Δ bkt_growth | Δ correct_rate |",
            "|-----------|-----------|--------------|----------------|",
        ]
        for c in report.conditions:
            if c.condition == report.baseline_condition:
                continue
            d_cwm = report.delta(c.condition, "contrast_with_misconception_rate")
            d_bkt = report.delta(c.condition, "bkt_growth")
            d_cor = report.delta(c.condition, "mean_correct_rate")
            lines.append(
                f"| `{c.condition}` | "
                f"{d_cwm:+.3f} | {d_bkt:+.4f} | {d_cor:+.3f} |"
            )

    lines += ["", "## Style distributions", ""]
    for c in report.conditions:
        lines.append(f"**`{c.condition}`**: " +
                     ", ".join(f"{s}={v}" for s, v in sorted(c.style_distribution.items())))

    path.write_text("\n".join(lines) + "\n")
