"""Phase 2 investor ablation on a **real** item bank (Gate A 2PL + Eedi distractors).

- `data/processed/real_item_params.parquet` (from `python -m ml.simulator.calibration.run_real`)
- ASSISTments for skill_id←problem_id: default S3 CSV (same as run_real)
- Eedi 2024: `s3://axonai-datasets-924300129944/eedi_mining_misconceptions/`
- `data/processed/real_bkt_params.parquet` (optional; defaults if missing)
- `data/processed/eedi_misconception_id_map.json` (optional)

  python -m ml.simulator.validation.investor_ablation_real
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.simulator.data.assistments_loader import (
    DEFAULT_MIN_RESPONSES_PER_ITEM,
    load_processed,
    load_responses,
)
from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.eedi_misconceptions_loader import load as load_eedi
from ml.simulator.data.item_bank import ItemBank, build_item_bank
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.misconceptions import SusceptibilitySampler
from ml.simulator.student.profile import StudentProfile
from ml.simulator.validation.investor_ablation import (
    CohortResult,
    InvestorAblationReport,
    _ttest_rel,
    simulate_cohort,
)

import networkx as nx

REPO = Path(__file__).resolve().parents[3]

ASSIST_CSV = (
    "s3://axonai-datasets-924300129944/assistments/"
    "2012-2013-data-with-predictions-4-final.csv"
)
EEDI_S3 = "s3://axonai-datasets-924300129944/eedi_mining_misconceptions/"
N_STUDENTS = 500
N_SESSIONS = 60
N_CONCEPTS_TARGET = 12
MAX_ITEMS_PER_CONCEPT = 50
SLOW_FRACTION = 0.10
SEED = 42

_ITEM_PARAMS = REPO / "data" / "processed" / "real_item_params.parquet"
_BKT_PARAMS = REPO / "data" / "processed" / "real_bkt_params.parquet"
_ID_MAP = REPO / "data" / "processed" / "eedi_misconception_id_map.json"
# Optional: save a copy with `from ml.simulator.data.assistments_loader import load_responses, cache_processed` after first S3 load.
_CACHED_ASSIST = REPO / "data" / "processed" / "assistments_responses.parquet"


@dataclass
class RealAblationProvenance:
    n_items_in_bank0: int
    n_items_with_eedi: int
    n_items_subsample: int
    concept_ids: list[int]
    n_misconception_ids_for_sampler: int
    assist_csv: str
    eedi_s3: str
    item_params_path: str
    bkt_path: str
    id_map_path: str | None
    error: str | None = None


@dataclass
class RealAblationResult:
    report: InvestorAblationReport
    provenance: RealAblationProvenance
    headline: dict[str, float]
    headline_interpretation: str


def _load_id_map() -> list[int] | None:
    if not _ID_MAP.is_file():
        return None
    p = json.loads(_ID_MAP.read_text(encoding="utf-8"))
    return [int(e["eedi_id"]) for e in p.get("entries", [])]


def _mids_from_bank(bank: ItemBank) -> set[int]:
    s: set[int] = set()
    for it in bank.items():
        for d in it.distractors:
            if d.misconception_id is not None:
                s.add(int(d.misconception_id))
    return s


def _chain_graph(skill_ids: list[int]) -> ConceptGraph:
    sids = sorted({int(s) for s in skill_ids})
    g = nx.DiGraph()
    g.add_node(sids[0])
    for a, b in zip(sids, sids[1:]):
        g.add_node(b)
        g.add_edge(int(a), int(b))
    return ConceptGraph(g)


def _bkt_map_for_skills(bkt_path: Path, skills: list[int]) -> dict[int, BKTParams]:
    m: dict[int, BKTParams] = {}
    if not bkt_path.is_file():
        for c in skills:
            m[c] = BKTParams(0.2, 0.1, 0.1, 0.25)
        return m
    df = pd.read_parquet(bkt_path)
    for c in skills:
        row = df[df["skill_id"] == c]
        if len(row) == 0:
            m[c] = BKTParams(0.2, 0.1, 0.1, 0.25)
        else:
            r0 = row.iloc[0]
            m[c] = BKTParams(
                float(r0["p_init"]),
                float(r0["p_transit"]),
                float(r0["p_slip"]),
                float(r0["p_guess"]),
            )
    return m


def _select_skills(bank: ItemBank, n: int) -> list[int]:
    from collections import Counter

    with_e: Counter[int] = Counter()
    all_c: Counter[int] = Counter()
    for it in bank.items():
        all_c[it.concept_id] += 1
        if it.distractors:
            with_e[it.concept_id] += 1
    ranked: list[int] = [k for k, _ in with_e.most_common(10_000)]
    if len(ranked) < n:
        for k, _ in all_c.most_common(10_000):
            if k not in ranked:
                ranked.append(k)
            if len(ranked) >= n:
                break
    if len(ranked) < 2:
        return ranked
    return sorted(ranked[:n])


def _subsample_bank(
    bank: ItemBank, keep_concepts: list[int], max_per: int, seed: int
) -> ItemBank:
    rng = np.random.default_rng(seed)
    sset = set(keep_concepts)
    out: list = []
    for c in keep_concepts:
        its = [it for it in bank.items_for_concept(c) if it.concept_id in sset]
        if len(its) > max_per:
            perm = rng.permutation(len(its))[:max_per]
            its = [its[i] for i in sorted(perm.tolist())]
        out.extend(its)
    return ItemBank(out)


def build_profiles(
    n_students: int, concept_ids: list[int], seed: int, misconception_ids: np.ndarray
) -> list[StudentProfile]:
    rng = np.random.default_rng(seed)
    n_slow = max(1, int(n_students * SLOW_FRACTION))
    sampler = SusceptibilitySampler(misconception_ids=misconception_ids)
    profiles: list[StudentProfile] = []
    for sid in range(n_students):
        theta = {c: float(rng.normal(0.0, 1.0)) for c in concept_ids}
        sc = float(np.mean(list(theta.values())))
        sus = sampler.draw(sc, rng)
        if sid < n_slow:
            rt_params = (math.log(35000), 0.3)
        else:
            rt_params = (math.log(8000), 0.4)
        profiles.append(
            StudentProfile(
                student_id=sid,
                true_theta=theta,
                estimated_theta={c: (v, 1.0) for c, v in theta.items()},
                bkt_state={c: BKTState(p_known=0.2) for c in concept_ids},
                elo_rating=1200.0,
                recall_half_life={c: 24.0 for c in concept_ids},
                last_retrieval={},
                learning_rate=0.1,
                slip=0.1,
                guess=0.25,
                engagement_decay=0.95,
                response_time_lognorm_params=rt_params,
                misconception_susceptibility=sus,
            )
        )
    return profiles


def _extract_misconception_ids(
    id_map: list[int] | None, bank: ItemBank
) -> np.ndarray:
    s = set(_mids_from_bank(bank))
    if id_map:
        s |= set(int(x) for x in id_map)
    if not s:
        s = {0}
    return np.array(sorted(s), dtype=np.int64)


def _pairwise_p(
    c_v1: CohortResult, c_v2: CohortResult, c_nt: CohortResult
) -> tuple[dict[str, float], dict[str, float]]:
    a = c_v2.per_student_elo_per_hr
    b = c_v1.per_student_elo_per_hr
    p_v1 = {
        "elo_gain_per_hr": _ttest_rel(a, b, "greater"),
        "time_to_mastery": _ttest_rel(
            c_v1.per_student_ttm_attempts, c_v2.per_student_ttm_attempts, "greater"
        ),
        "retention_7d": _ttest_rel(
            c_v2.per_student_retention_7d, c_v1.per_student_retention_7d, "greater"
        ),
        "retention_30d": _ttest_rel(
            c_v2.per_student_retention_30d, c_v1.per_student_retention_30d, "greater"
        ),
    }
    p_nt = {
        "elo_gain_per_hr": _ttest_rel(a, c_nt.per_student_elo_per_hr, "greater"),
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
    return p_v1, p_nt


def _headline_lifts(c_v1: CohortResult, c_v2: CohortResult) -> dict[str, float]:
    m1 = c_v1.to_summary()
    m2 = c_v2.to_summary()
    e1, e2 = m1["mean_elo_gain_per_hr"], m2["mean_elo_gain_per_hr"]
    elo_pct = 100.0 * (e2 - e1) / (abs(e1) + 1e-6)
    t1 = m1.get("median_time_to_mastery_attempts")
    t2 = m2.get("median_time_to_mastery_attempts")
    if t1 is not None and t2 is not None:
        ttm_pct = 100.0 * (float(t1) - float(t2)) / (float(t1) + 1e-6)
    else:
        ttm_pct = float("nan")
    r1_7 = m1["mean_retention_7d"]
    r2_7 = m2["mean_retention_7d"]
    r_pct = 100.0 * (r2_7 - r1_7) / (r1_7 + 1e-9) if r1_7 is not None else float("nan")
    return {
        "elo_gain_pct_v2_over_v1": float(elo_pct),
        "ttm_pct_faster_median": float(ttm_pct),
        "retention7_pct_lift": float(r_pct),
    }


def run_investor_ablation_real(
    n_students: int = N_STUDENTS,
    n_sessions: int = N_SESSIONS,
    n_concepts: int = N_CONCEPTS_TARGET,
    max_items_per: int = MAX_ITEMS_PER_CONCEPT,
    seed: int = SEED,
    item_params_path: Path = _ITEM_PARAMS,
    bkt_path: Path = _BKT_PARAMS,
    assist_csv: str = ASSIST_CSV,
    eedi_s3: str = EEDI_S3,
) -> RealAblationResult | None:
    eedi_s3 = eedi_s3.rstrip("/") + "/"
    if not item_params_path.is_file():
        return None
    item_params = pd.read_parquet(item_params_path)
    for col in ("item_id", "a", "b"):
        if col not in item_params.columns:
            return None
    if item_params["item_id"].duplicated().any():
        item_params = item_params.drop_duplicates(subset=["item_id"], keep="first")

    if _CACHED_ASSIST.is_file():
        print(
            f"[real_ablation] using cached responses {_CACHED_ASSIST}",
            flush=True,
        )
        responses = load_processed(_CACHED_ASSIST)
    else:
        print(
            "[real_ablation] loading ASSISTments (S3); to skip next time run once:\n"
            f"  from ml.simulator.data.assistments_loader import load_responses, cache_processed\n"
            f"  cache_processed(load_responses('...', min_responses_per_item=150), '{_CACHED_ASSIST}')",
            flush=True,
        )
        responses = load_responses(
            assist_csv, min_responses_per_item=DEFAULT_MIN_RESPONSES_PER_ITEM
        )

    print("[real_ablation] loading Eedi (S3 prefix)…", flush=True)
    eedi = load_eedi(questions_path=eedi_s3)

    bank0 = build_item_bank(item_params, responses, eedi_frames=eedi)
    n_e = sum(1 for it in bank0.items() if it.distractors)
    if len(bank0) < 20:
        return None
    sk = _select_skills(bank0, n_concepts)
    if len(sk) < 2:
        return None
    bank = _subsample_bank(bank0, sk, max_items_per, seed)
    g = _chain_graph(sk)
    bkt = _bkt_map_for_skills(bkt_path, sk)
    id_list = _load_id_map()
    mids = _extract_misconception_ids(id_list, bank)
    prov = RealAblationProvenance(
        n_items_in_bank0=len(bank0),
        n_items_with_eedi=n_e,
        n_items_subsample=len(bank),
        concept_ids=list(sk),
        n_misconception_ids_for_sampler=int(len(mids)),
        assist_csv=assist_csv,
        eedi_s3=eedi_s3,
        item_params_path=str(item_params_path),
        bkt_path=str(bkt_path) if bkt_path.is_file() else "(BKT defaults)",
        id_map_path=str(_ID_MAP) if _ID_MAP.is_file() else None,
        error=None,
    )
    print(
        f"[real_ablation] bank0={len(bank0)} items, Eedi-on-join={n_e}; using {len(bank)} in {len(sk)} skills",
        flush=True,
    )
    profiles = build_profiles(n_students, sk, seed, mids)

    c_v1 = simulate_cohort("v1_uniform", bank, g, bkt, profiles, n_sessions, seed, "uniform", False, "zpd")
    c_v2 = simulate_cohort("v2_misconception_only", bank, g, bkt, profiles, n_sessions, seed, "misconception_weighted", True, "zpd")
    c_nt = simulate_cohort("no_tutor_control", bank, g, bkt, profiles, n_sessions, seed, "uniform", False, "random")
    c_full = CohortResult(
        "v2_full (learning; tutor/rewriter not in sim path)",
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
    p_v1, p_nt = _pairwise_p(c_v1, c_v2, c_nt)
    rep.p_paired_t_v2full_vs_v1 = p_v1
    rep.p_paired_t_v2full_vs_notutor = p_nt
    hl = _headline_lifts(c_v1, c_v2)
    interp = (
        "Differences v1↔v2 on Elo/retention can appear if wrong-answer paths use extra random draws, "
        "so subsequent Bernoulli outcomes diverge. If lifts stay ~0% while Eedi is present, 2PL correctness "
        "remains the dominant state update; the headline +55% / −25% / +19% is **not** supported in sim."
    )
    return RealAblationResult(
        report=rep,
        provenance=prov,
        headline=hl,
        headline_interpretation=interp,
    )


def _write_real_md(r: RealAblationResult, path: Path) -> None:
    p = r.provenance
    h = r.headline
    def _rp(path_str: str) -> str:
        if path_str.startswith("("):
            return path_str
        pl = Path(path_str)
        try:
            return pl.resolve().relative_to(REPO.resolve()).as_posix()
        except (OSError, ValueError):
            return pl.as_posix()

    bkt_s = _rp(p.bkt_path) if not str(p.bkt_path).startswith("(") else p.bkt_path
    lines: list[str] = [
        "# Phase 2 — investor ablation (**real** 2PL bank + Eedi)",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}Z",
        "",
        "## 0. Provenance",
        "",
        f"- **Item params (Gate A):** `{_rp(p.item_params_path)}`",
        f"- **BKT map:** `{bkt_s}`",
        f"- **Eedi (distractor→misconception):** `{p.eedi_s3}`",
        f"- **ASSISTments (skill join):** `{p.assist_csv}`",
        f"- **Pre-subsample bank0:** {p.n_items_in_bank0} items; **with Eedi distractors (QuestionId=problem_id overlap):** {p.n_items_with_eedi}",
        f"- **Subsample used in sim:** {p.n_items_subsample} items; **concepts (sorted chain):** `{p.concept_ids}`",
        f"- **Sparse Eedi overlap:** on this dataset only **{p.n_items_with_eedi}** matched items carry tagged distractors; most practice draws use ASSISTments-only items with *empty* `distractors` — so the weighted distractor model rarely runs. Expect **v1_uniform ≈ v2_misconception** on Elo unless overlap grows.",
        f"- **Misconception IDs in sampler (count):** {p.n_misconception_ids_for_sampler}; id map: {p.id_map_path or 'tags from items + Eedi only'}",
        f"- *Graph:* linear chain `skill[0]→…→skill[n-1]` in sorted skill_id order (ablation control, not curriculum truth).",
        "",
        "## 1. Headline: v2 – v1 (paired, same 500 students)",
        f"- Elo gain/hr, %Δ vs v1: **{h.get('elo_gain_pct_v2_over_v1', float('nan')):.4f}**",
        f"- TTM (median att.), % “faster” than v1: **{h.get('ttm_pct_faster_median', float('nan')):.4f}**",
        f"- Retention @ 7d (cohort mean), % lift vs v1: **{h.get('retention7_pct_lift', float('nan')):.4f}**",
        "",
    ]
    lines += [
        "### Investor headline claim check (+55% / −25% / +19% vs baseline)",
        "",
    ]
    lines += [
        "Compare magnitudes in §1 to the investor deck. " + r.headline_interpretation,
        "",
        _tables_md(r.report),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _tables_md(rep: InvestorAblationReport) -> str:
    t: list[str] = [
        "## 2. Conditions",
        "",
        "| Condition | Elo gain/hr (mean) | TTM (median) | Ret @7d | Ret @30d |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("v1_uniform", "v2_misconception_only", "v2_full", "no_tutor_control"):
        c = rep.by_condition[key]
        s = c.to_summary()
        ttm = s.get("median_time_to_mastery_attempts")
        ts = f"{ttm:.1f}" if ttm is not None else "nan"
        t.append(
            f"| `{key}` | {s['mean_elo_gain_per_hr']:.4f} | {ts} | {s['mean_retention_7d']:.4f} | {s['mean_retention_30d']:.4f} |"
        )
    t += [
        "",
        "## 3. Paired p: v2 vs v1",
        "",
    ]
    for k, v in rep.p_paired_t_v2full_vs_v1.items():
        t.append(f"- `{k}`: {v}")
    t += ["", "## 4. Paired p: v2 vs no_tutor_control", ""]
    for k, v in rep.p_paired_t_v2full_vs_notutor.items():
        t.append(f"- `{k}`: {v}")
    return "\n".join(t)


def main() -> int:
    out = REPO / "validation" / "phase_2" / "ablation_results_real_bank.md"
    jf = REPO / "validation" / "phase_2" / "ablation_results.json"
    r = run_investor_ablation_real()
    if r is None:
        out.write_text(
            f"""# Real-bank ablation — not run
Missing or insufficient Gate A data at `{_ITEM_PARAMS}`.
Generate with: `python -m ml.simulator.calibration.run_real` (requires ASSISTments S3 + disk under `data/processed/`).
""",
            encoding="utf-8",
        )
        print("Wrote stub to", out)
        return 1
    _write_real_md(r, out)
    d: dict[str, Any] = r.report.to_dict()
    d["source"] = "real_bank_eedi"
    prov = asdict(r.provenance)
    for k in ("item_params_path", "bkt_path", "id_map_path"):
        if k in prov and prov[k] and not str(prov[k]).startswith("("):
            try:
                prov[k] = Path(prov[k]).resolve().relative_to(REPO.resolve()).as_posix()
            except (OSError, ValueError):
                pass
    d["provenance"] = prov
    d["headline_lifts"] = {
        "elo_gain_pct_v2_over_v1": _json_num(r.headline.get("elo_gain_pct_v2_over_v1", 0.0)),
        "ttm_pct_faster_median": _json_num(r.headline.get("ttm_pct_faster_median", 0.0)),
        "retention7_pct_lift": _json_num(r.headline.get("retention7_pct_lift", 0.0)),
    }
    d["headline_interpretation"] = r.headline_interpretation
    jf.write_text(json.dumps(d, indent=2, allow_nan=False), encoding="utf-8")
    print("Wrote", out, "and", jf)
    return 0


def _json_num(x: float) -> float | None:
    if x != x:
        return None
    return float(x)


if __name__ == "__main__":
    raise SystemExit(main())
