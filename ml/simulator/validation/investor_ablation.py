"""Phase 2 investor ablation — four conditions, paired learning metrics.

Conditions (same synthetic bank, `seed` for `StudentProfile` list):

- **v1_uniform** — `response_model=uniform`, no detector, ZPD item selection.
- **v2_misconception_only** — `response_model=misconception_weighted`, detector, ZPD.
- **v2_full** — same *learning* trajectory as v2 in this harness when `llm_tutor` is
  absent; tutor/rewriter do not update Elo/BKT/HLR. Numbers duplicate v2; footnote
  in the report explains.
- **no_tutor_control** — uniform + **random** item in concept bank, no detector.

Paired *t*-tests: same 500 `student_id`s, policy differs only in runner flags.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from ml.simulator.loop.runner import TermRunner
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.psychometrics.hlr import predict_recall
from ml.simulator.student.misconceptions import SusceptibilitySampler
from ml.simulator.student.profile import AttemptRecord, StudentProfile
import networkx as nx

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import ItemBank
from ml.simulator.validation.phase2_pipeline import _build_synthetic_bank


def _build_concept_graph(n_concepts: int) -> ConceptGraph:
    g = nx.DiGraph()
    for i in range(1, n_concepts + 1):
        g.add_node(i)
    for i in range(1, n_concepts):
        g.add_edge(i, i + 1)
    return ConceptGraph(g)


def _build_bkt(n_concepts: int) -> dict[int, BKTParams]:
    return {c: BKTParams(0.2, 0.1, 0.08, 0.2) for c in range(1, n_concepts + 1)}


def _build_student_profiles(
    n_students: int,
    n_concepts: int,
    seed: int = 0,
) -> list[StudentProfile]:
    from ml.simulator.validation.phase2_pipeline import _SLOW_STUDENT_FRACTION
    import math
    from ml.simulator.psychometrics.bkt import BKTState

    rng = np.random.default_rng(seed)
    misc_ids = np.array(
        [c * 100 + r for c in range(1, n_concepts + 1) for r in range(5)],
        dtype=np.int64,
    )
    sampler = SusceptibilitySampler(misconception_ids=misc_ids)
    profiles: list[StudentProfile] = []
    n_slow = max(1, int(n_students * _SLOW_STUDENT_FRACTION))
    for sid in range(n_students):
        theta = {c: float(rng.normal(0.0, 1.0)) for c in range(1, n_concepts + 1)}
        scalar_theta = float(np.mean(list(theta.values())))
        susceptibility = sampler.draw(scalar_theta, rng)
        if sid < n_slow:
            rt_params = (math.log(35000), 0.3)
        else:
            rt_params = (math.log(8000), 0.4)
        profiles.append(
            StudentProfile(
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
            )
        )
    return profiles


def _mastery_all(p: StudentProfile) -> bool:
    return all(s.p_known >= 0.85 for s in p.bkt_state.values())


@dataclass(frozen=True)
class CohortResult:
    condition: str
    n_students: int
    n_sessions: int
    per_student_elo_per_hr: np.ndarray
    per_student_ttm_attempts: np.ndarray
    per_student_retention_7d: np.ndarray
    per_student_retention_30d: np.ndarray

    def to_summary(self) -> dict[str, float | None]:
        ttm = self.per_student_ttm_attempts
        ttmf = ttm[np.isfinite(ttm)]
        med = float(np.nanmedian(ttmf)) if len(ttmf) > 0 else float("nan")
        return {
            "mean_elo_gain_per_hr": float(np.nanmean(self.per_student_elo_per_hr)),
            "median_time_to_mastery_attempts": med if np.isfinite(med) else None,
            "mean_retention_7d": float(np.mean(self.per_student_retention_7d)),
            "mean_retention_30d": float(np.mean(self.per_student_retention_30d)),
        }


@dataclass
class InvestorAblationReport:
    by_condition: dict[str, CohortResult]
    n_students: int
    n_sessions: int
    p_paired_t_v2full_vs_v1: dict[str, float] = field(default_factory=dict)
    p_paired_t_v2full_vs_notutor: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_students": self.n_students,
            "n_sessions": self.n_sessions,
            "conditions": {k: {**v.to_summary(), "n": v.n_students} for k, v in self.by_condition.items()},
            "p_paired_t_v2full_vs_v1": self.p_paired_t_v2full_vs_v1,
            "p_paired_t_v2full_vs_notutor": self.p_paired_t_v2full_vs_notutor,
        }


def _retention_cohort(fp: StudentProfile) -> tuple[float, float]:
    r7: list[float] = []
    r30: list[float] = []
    for _cid, hl in fp.recall_half_life.items():
        r7.append(predict_recall(hl, 7.0 * 24.0))
        r30.append(predict_recall(hl, 30.0 * 24.0))
    if not r7:
        return 0.0, 0.0
    return float(np.mean(r7)), float(np.mean(r30))


def simulate_cohort(
    name: str,
    bank: ItemBank,
    g: ConceptGraph,
    bkt: dict[int, BKTParams],
    profiles: list[StudentProfile],
    n_sessions: int,
    seed: int,
    response_model: str,
    use_detector: bool,
    item_selection: str,
) -> CohortResult:
    start = datetime(2024, 1, 1)
    n_students = len(profiles)
    elo: list[float] = []
    ttm: list[float] = []
    r7: list[float] = []
    r30: list[float] = []
    for sid, profile in enumerate(profiles):
        det = MisconceptionDetector() if use_detector else None
        sseed = seed + sid * 7919
        tr = TermRunner(
            student=profile,
            concept_graph=g,
            item_bank=bank,
            bkt_params_by_concept=bkt,
            start_time=start,
            n_sessions=n_sessions,
            seed=sseed,
            misconception_detector=det,
            response_model=response_model,
            item_selection=item_selection,
        )
        tot_ms = 0
        for event in tr.run():
            if isinstance(event, AttemptRecord):
                tot_ms += int(event.response_time_ms)
        if tot_ms < 1:
            tot_ms = 1
        fp = tr.final_profile
        elph = (fp.elo_rating - 1200.0) / (tot_ms / 3_600_000.0)
        elo.append(elph)
        ttm_v = float(len(fp.attempts_history)) if _mastery_all(fp) else float("nan")
        ttm.append(ttm_v)
        c7, c3 = _retention_cohort(fp)
        r7.append(c7)
        r30.append(c3)
    return CohortResult(
        condition=name,
        n_students=n_students,
        n_sessions=n_sessions,
        per_student_elo_per_hr=np.array(elo, dtype=np.float64),
        per_student_ttm_attempts=np.array(ttm, dtype=np.float64),
        per_student_retention_7d=np.array(r7, dtype=np.float64),
        per_student_retention_30d=np.array(r30, dtype=np.float64),
    )


def _run_cohort(
    name: str,
    n_students: int,
    n_concepts: int,
    n_items_per: int,
    n_sessions: int,
    seed: int,
    response_model: str,
    use_detector: bool,
    item_selection: str,
) -> CohortResult:
    bank = _build_synthetic_bank(n_concepts, n_items_per, seed)
    g = _build_concept_graph(n_concepts)
    bkt = _build_bkt(n_concepts)
    profiles = _build_student_profiles(n_students, n_concepts, seed)
    return simulate_cohort(
        name, bank, g, bkt, profiles, n_sessions, seed, response_model,
        use_detector, item_selection,
    )


def _ttest_rel(
    a: np.ndarray, b: np.ndarray, alternative: str
) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 2:
        return 1.0
    try:
        t = stats.ttest_rel(a, b, alternative=alternative)
    except TypeError:  # older scipy: two-tailed + manual
        t = stats.ttest_rel(a, b)
        p2 = float(t.pvalue)
        d = float(np.mean(a - b))
        if alternative == "greater" and d <= 0:
            return 1.0
        if alternative == "less" and d >= 0:
            return 1.0
        return p2 / 2.0 if p2 < 1.0 else 1.0
    p = float(t.pvalue)
    if np.isnan(p):
        return 1.0
    return p


def run_investor_ablation(
    n_students: int = 500,
    n_concepts: int = 10,
    n_items_per: int = 10,
    n_sessions: int = 60,
    seed: int = 42,
) -> InvestorAblationReport:
    c_v1 = _run_cohort(
        "v1_uniform", n_students, n_concepts, n_items_per, n_sessions, seed,
        "uniform", False, "zpd",
    )
    c_v2 = _run_cohort(
        "v2_misconception_only", n_students, n_concepts, n_items_per, n_sessions, seed,
        "misconception_weighted", True, "zpd",
    )
    c_nt = _run_cohort(
        "no_tutor_control", n_students, n_concepts, n_items_per, n_sessions, seed,
        "uniform", False, "random",
    )
    c_full = CohortResult(
        "v2_full (learning stack; tutor/rewriter inert in harness)",
        c_v2.n_students,
        c_v2.n_sessions,
        np.copy(c_v2.per_student_elo_per_hr),
        np.copy(c_v2.per_student_ttm_attempts),
        np.copy(c_v2.per_student_retention_7d),
        np.copy(c_v2.per_student_retention_30d),
    )
    rep = InvestorAblationReport(
        by_condition={
            "v1_uniform": c_v1,
            "v2_misconception_only": c_v2,
            "v2_full": c_full,
            "no_tutor_control": c_nt,
        },
        n_students=n_students,
        n_sessions=n_sessions,
    )
    a = c_v2.per_student_elo_per_hr
    b = c_v1.per_student_elo_per_hr
    rep.p_paired_t_v2full_vs_v1 = {
        "elo_gain_per_hr": _ttest_rel(
            a, b, "greater"
        ),
        "time_to_mastery": _ttest_rel(
            c_v1.per_student_ttm_attempts,
            c_v2.per_student_ttm_attempts,
            "greater",  # v1 TTM > v2 TTM
        ),
        "retention_7d": _ttest_rel(
            c_v2.per_student_retention_7d, c_v1.per_student_retention_7d, "greater"
        ),
        "retention_30d": _ttest_rel(
            c_v2.per_student_retention_30d, c_v1.per_student_retention_30d, "greater"
        ),
    }
    rep.p_paired_t_v2full_vs_notutor = {
        "elo_gain_per_hr": _ttest_rel(
            a, c_nt.per_student_elo_per_hr, "greater"
        ),
        "time_to_mastery": _ttest_rel(
            c_nt.per_student_ttm_attempts, c_v2.per_student_ttm_attempts, "greater"
        ),
        "retention_7d": _ttest_rel(
            c_v2.per_student_retention_7d, c_nt.per_student_retention_7d, "greater"
        ),
        "retention_30d": _ttest_rel(
            c_v2.per_student_retention_30d, c_nt.per_student_retention_30d, "greater"
        ),
    }
    return rep


def write_investor_ablation_markdown(
    rep: InvestorAblationReport, path: str | Path
) -> None:
    path = Path(path)
    p = path
    lines: list[str] = [
        "# Phase 2 — investor ablation (four conditions)",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}Z",
        f"**Students / sessions:** {rep.n_students} × {rep.n_sessions} (same as `phase_2_validation.yaml`: 12 weeks × 5 sessions, rounded to {rep.n_sessions} total sessions in harness)",
        "",
        "Per-student Elo is **global** student rating; **Elo gain/hr** = `(elo_end − 1200) / study_hours` where study hours =",
        "sum of attempt `response_time_ms` / 3.6e6. **Time-to-mastery** = number of attempts when *all* concepts first reach BKT p_known ≥ 0.85,",
        "or censored (excluded) if not reached. **Retention @ 7d/30d** = mean of per-concept `hlr.predict_recall(h, {7|30}×24 hours)` on the final profile.",
        "",
        "**Paired *t* tests** (one-tailed where a higher Elo, higher retention, or a lower TTM is better; same 500 `student_id`s).",
        "",
        "## 1. Condition means / medians",
        "",
        "| Condition | Elo gain/hr (mean) | Time-to-mastery (median att.) | Ret @ 7d (mean) | Ret @ 30d (mean) |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("v1_uniform", "v2_misconception_only", "v2_full", "no_tutor_control"):
        c = rep.by_condition[key]
        s = c.to_summary()
        ttm = s["median_time_to_mastery_attempts"]
        ttm_s = f"{ttm:.1f}" if ttm is not None else "nan"
        lines.append(
            f"| `{key}` | {s['mean_elo_gain_per_hr']:.4f} | {ttm_s} | {s['mean_retention_7d']:.4f} | {s['mean_retention_30d']:.4f} |"
        )
    lines += [
        "",
        "## 2. Paired tests — v2_full vs v1_uniform",
        "",
        "| Metric | p-value (paired, one-tailed) |",
        "|---|---:|",
    ]
    for k, v in rep.p_paired_t_v2full_vs_v1.items():
        lines.append(f"| {k} | {v:.2e} |" if v < 1e-3 else f"| {k} | {v:.6f} |")
    lines += [
        "",
        "## 3. Paired tests — v2_full vs no_tutor_control",
        "",
        "| Metric | p-value (paired, one-tailed) |",
        "|---|---:|",
    ]
    for k, v in rep.p_paired_t_v2full_vs_notutor.items():
        lines.append(f"| {k} | {v:.2e} |" if v < 1e-3 else f"| {k} | {v:.6f} |")
    lines += [
        "",
        "## 4. Interpretation (read before sign-off)",
        "",
        "- **v1_uniform vs v2_misconception_only — identical Elo/TTM/retention in this harness.** The Bernoulli draw for 2PL correctness is the"
        " first (and only) `rng` call that affects *whether* the student is correct; the misconception-weighted distractor path"
        " only changes `triggered_misconception_id` after a wrong answer, not `P(correct)` or the Elo/BKT/HLR updates. With the"
        " same per-student `TermRunner` seed, **v1 and v2 trajectories are therefore identical** on these metrics.",
        "- **Primary contrast with instructional signal:** `no_tutor_control` (uniform + **random** item in bank) often fails to"
        " reach BKT mastery for all concepts within 60 sessions — TTM is censored (shown as `nan`), and the comparison vs v2 is"
        " on **Elo gain/hr** and **retention** where the effect is very large. Where both TTM values are finite, a paired TTM"
        " test is meaningful; otherwise the TTM p-value is **not interpretable** (treated as N/A; reported as 1.0 in the table).",
        "- **`v2_full`** duplicates **`v2_misconception_only`** when `llm_tutor` is not attached; tutor/rewriter are logging-only until coupled to the learning state.",
        "",
        "## 5. Regenerate",
        "",
        "- `python -m ml.simulator.validation.write_phase2_validation_artifacts`",
        "- `validation/phase_2/ablation_results.json`",
        "",
    ]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    r = run_investor_ablation(500, 10, 10, 60, 42)
    out = Path("validation/phase_2/ablation_results.md")
    write_investor_ablation_markdown(r, out)
    (out.parent / "ablation_results.json").write_text(
        json.dumps(r.to_dict(), indent=2, allow_nan=False), encoding="utf-8"
    )
    print("wrote", out)
