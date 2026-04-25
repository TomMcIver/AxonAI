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
import traceback
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
from ml.simulator.data.item_bank import (
    ItemBank,
    build_item_bank,
    load_verified_assistments_eedi_map,
)
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
# Human- or QC-approved ASSISTments problem_id → Eedi QuestionId; verified-only rows.
_VERIFIED_CROSSWALK = (
    REPO / "data" / "processed" / "gate_a_eedi_verified_crosswalk.csv"
)


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
    verified_crosswalk_path: str | None
    n_rows_verified_crosswalk: int
    use_verified_crosswalk_bank: bool
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


def _select_skills(
    bank: ItemBank, n: int, prefer_items_with_distractors: bool = True
) -> list[int]:
    from collections import Counter

    with_e: Counter[int] = Counter()
    all_c: Counter[int] = Counter()
    for it in bank.items():
        all_c[it.concept_id] += 1
        if it.distractors:
            with_e[it.concept_id] += 1
    if prefer_items_with_distractors:
        ranked: list[int] = [k for k, _ in with_e.most_common(10_000)]
        if len(ranked) < n:
            for k, _ in all_c.most_common(10_000):
                if k not in ranked:
                    ranked.append(k)
                if len(ranked) >= n:
                    break
    else:
        # For verified-crosswalk runs, rank by total verified items per skill,
        # not by whether Eedi distractor tags are present.
        ranked = [k for k, _ in all_c.most_common(10_000)]
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
    verified_crosswalk_path: Path = _VERIFIED_CROSSWALK,
) -> RealAblationResult | None:
    print("[real_ablation] starting run_investor_ablation_real", flush=True)
    eedi_s3 = eedi_s3.rstrip("/") + "/"
    if not item_params_path.is_file():
        return None
    item_params = pd.read_parquet(item_params_path)
    print(
        f"[real_ablation] Gate A item params columns: {list(item_params.columns)}",
        flush=True,
    )
    print(
        "[real_ablation] Gate A item params first5:\n"
        f"{item_params.head(5).to_string(index=False)}",
        flush=True,
    )
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

    use_xw = False
    n_xw = 0
    assist_eedi: dict[int, int] | None = None
    if verified_crosswalk_path.is_file():
        try:
            xw_df = pd.read_csv(verified_crosswalk_path, low_memory=False)
            xw_cols = {str(c).strip().lower(): str(c).strip() for c in xw_df.columns}
            xw_a_col = next(
                (
                    xw_cols[k]
                    for k in (
                        "assistments_problem_id",
                        "assistments_item_id",
                        "problem_id",
                        "item_id",
                    )
                    if k in xw_cols
                ),
                None,
            )
            if xw_a_col is not None:
                print(
                    f"[real_ablation] crosswalk first5 {xw_a_col}: "
                    f"{xw_df[xw_a_col].head(5).tolist()}",
                    flush=True,
                )
            assist_eedi = load_verified_assistments_eedi_map(verified_crosswalk_path)
            n_xw = len(assist_eedi)
            gate_ids = set(
                pd.to_numeric(item_params["item_id"], errors="coerce")
                .dropna()
                .astype(int)
                .tolist()
            )
            crosswalk_ids = set(int(k) for k in assist_eedi.keys())
            direct_overlap = len(crosswalk_ids & gate_ids)
            print(
                f"[real_ablation] crosswalk->GateA direct overlap on item_id: "
                f"{direct_overlap}/{len(crosswalk_ids)}",
                flush=True,
            )
            if direct_overlap == 0:
                print(
                    "[real_ablation] no direct overlap; crosswalk IDs likely reference a "
                    "different ASSISTments id namespace (for example problem_log_id).",
                    flush=True,
                )
            if "problem_log_id" in responses.columns:
                bridge = responses[["problem_log_id", "problem_id"]].copy()
                bridge["problem_log_id"] = pd.to_numeric(
                    bridge["problem_log_id"], errors="coerce"
                )
                bridge["problem_id"] = pd.to_numeric(
                    bridge["problem_id"], errors="coerce"
                )
                bridge = bridge.dropna(subset=["problem_log_id", "problem_id"])
                if not bridge.empty:
                    bridge["problem_log_id"] = bridge["problem_log_id"].astype(int)
                    bridge["problem_id"] = bridge["problem_id"].astype(int)
                    modal = (
                        bridge.groupby(["problem_log_id", "problem_id"])
                        .size()
                        .reset_index(name="n")
                        .sort_values(
                            ["problem_log_id", "n", "problem_id"],
                            ascending=[True, False, True],
                        )
                        .drop_duplicates("problem_log_id", keep="first")
                    )
                    log_to_problem = dict(
                        zip(
                            modal["problem_log_id"].astype(int),
                            modal["problem_id"].astype(int),
                        )
                    )
                    mapped = {log_to_problem[k] for k in crosswalk_ids if k in log_to_problem}
                    mapped_overlap = len(mapped & gate_ids)
                    print(
                        f"[real_ablation] overlap after problem_log_id->problem_id remap: "
                        f"{mapped_overlap}/{len(crosswalk_ids)}",
                        flush=True,
                    )
            else:
                print(
                    "[real_ablation] responses has no problem_log_id column; cannot test "
                    "problem_log_id->problem_id remap on this input",
                    flush=True,
                )
            if n_xw > 0:
                use_xw = True
                print(
                    f"[real_ablation] using verified crosswalk: {verified_crosswalk_path} "
                    f"({n_xw} assist->Eedi rows); bank = intersection with Gate A + modal skill",
                    flush=True,
                )
            else:
                print(
                    f"[real_ablation] crosswalk {verified_crosswalk_path} has no "
                    f"verified rows; falling back to legacy problem_id=QuestionId join",
                    flush=True,
                )
        except (OSError, KeyError, ValueError) as ex:
            print(
                f"[real_ablation] could not read crosswalk ({ex}); using legacy ID join",
                flush=True,
            )
    else:
        print(
            f"[real_ablation] no file at {verified_crosswalk_path}; using legacy ID join",
            flush=True,
        )

    if use_xw and assist_eedi is not None:
        bank0 = build_item_bank(
            item_params,
            responses,
            eedi_frames=eedi,
            assist_to_eedi_verified=assist_eedi,
            only_items_in_verified_map=True,
        )
    else:
        bank0 = build_item_bank(item_params, responses, eedi_frames=eedi)
    n_e = sum(1 for it in bank0.items() if it.distractors)
    print(
        f"[real_ablation] build bank complete: bank0={len(bank0)}, with_distractors={n_e}",
        flush=True,
    )
    min_bank_items = 5 if use_xw else 20
    if len(bank0) < min_bank_items:
        print(
            f"[real_ablation] bank too small for run: {len(bank0)} < {min_bank_items} "
            f"(use_verified_crosswalk_bank={use_xw})",
            flush=True,
        )
        return None
    sk = _select_skills(
        bank0,
        n_concepts,
        prefer_items_with_distractors=not use_xw,
    )
    print(
        f"[real_ablation] select skills complete: selected={len(sk)} -> {sk}",
        flush=True,
    )
    if use_xw:
        skill_counts: dict[int, int] = {
            int(c): int(len(bank0.items_for_concept(c))) for c in sk
        }
        print(
            f"[real_ablation] verified-crosswalk selected skill counts: {skill_counts}",
            flush=True,
        )
    else:
        legacy_tagged_counts: dict[int, int] = {}
        for c in sk:
            legacy_tagged_counts[int(c)] = int(
                sum(1 for it in bank0.items_for_concept(c) if it.distractors)
            )
        print(
            f"[real_ablation] legacy selected skill tagged counts: {legacy_tagged_counts}",
            flush=True,
        )
    if len(sk) < 2:
        return None
    bank = _subsample_bank(bank0, sk, max_items_per, seed)
    g = _chain_graph(sk)
    bkt = _bkt_map_for_skills(bkt_path, sk)
    id_list = _load_id_map()
    mids = _extract_misconception_ids(id_list, bank)
    xw_relp: str | None
    if verified_crosswalk_path.is_file():
        try:
            xw_relp = str(
                verified_crosswalk_path.resolve().relative_to(REPO.resolve())
            )
        except (OSError, ValueError):
            xw_relp = str(verified_crosswalk_path)
    else:
        xw_relp = None
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
        verified_crosswalk_path=xw_relp,
        n_rows_verified_crosswalk=n_xw,
        use_verified_crosswalk_bank=use_xw,
        error=None,
    )
    print(
        f"[real_ablation] bank0={len(bank0)} items, with distractor tags={n_e}; using {len(bank)} in {len(sk)} skills",
        flush=True,
    )
    profiles = build_profiles(n_students, sk, seed, mids)
    print(
        f"[real_ablation] build profiles complete: n_profiles={len(profiles)}",
        flush=True,
    )

    print("[real_ablation] simulate cohort start: v1_uniform", flush=True)
    c_v1 = simulate_cohort("v1_uniform", bank, g, bkt, profiles, n_sessions, seed, "uniform", False, "zpd")
    print("[real_ablation] simulate cohort complete: v1_uniform", flush=True)
    print("[real_ablation] simulate cohort start: v2_misconception_only", flush=True)
    c_v2 = simulate_cohort("v2_misconception_only", bank, g, bkt, profiles, n_sessions, seed, "misconception_weighted", True, "zpd")
    print("[real_ablation] simulate cohort complete: v2_misconception_only", flush=True)
    print("[real_ablation] simulate cohort start: no_tutor_control", flush=True)
    c_nt = simulate_cohort("no_tutor_control", bank, g, bkt, profiles, n_sessions, seed, "uniform", False, "random")
    print("[real_ablation] simulate cohort complete: no_tutor_control", flush=True)
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
    if use_xw and n_e > 0 and n_e == len(bank0):
        xw_note = (
            f"With the verified crosswalk, all {n_e} bank0 items reference Eedi distractor/misconception "
            f"metadata (tags may still be empty if Eedi has no options for that QuestionId). "
        )
    elif use_xw:
        xw_note = "Verified crosswalk: bank is restricted to mapped items; "
    else:
        xw_note = (
            "Legacy join uses rare problem_id=QuestionId overlap; most items have empty distractors. "
        )
    interp = (
        xw_note
        + "Differences v1 to v2 on Elo/retention can appear if wrong-answer paths use extra random draws, "
        "so subsequent Bernoulli outcomes diverge. If lifts stay around 0% while v2 is active, 2PL correctness "
        "remains the dominant state update; a strong investor-style headline is **not** supported in sim."
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
        f"- **Verified crosswalk file:** `{p.verified_crosswalk_path or 'not on disk'}`; **use verified-only bank:** {p.use_verified_crosswalk_bank} (**{p.n_rows_verified_crosswalk}** assist to Eedi rows loaded)",
        f"- **Pre-subsample bank0:** {p.n_items_in_bank0} items; **with non-empty distractor lists (tags optional per option):** {p.n_items_with_eedi}",
        f"- **Subsample used in sim:** {p.n_items_subsample} items; **concepts (sorted chain):** `{p.concept_ids}`",
    ]
    if p.use_verified_crosswalk_bank and p.verified_crosswalk_path:
        lines += [
            (
                "- **Eedi join mode:** `gate_a_eedi_verified_crosswalk.csv` (verified only). "
                "Each bank item takes distractor and misconception fields from the **mapped** Eedi "
                "QuestionId (not identity problem_id=QuestionId)."
            ),
        ]
    else:
        lines += [
            (
                "- **Eedi join mode:** legacy (QuestionId = ASSISTments `problem_id` if equal). "
                "On this release overlap is small; most items have empty `distractors` unless a crosswalk is used."
            ),
        ]
    lines += [
        f"- **Misconception IDs in sampler (count):** {p.n_misconception_ids_for_sampler}; id map: {p.id_map_path or 'tags from items + Eedi only'}",
        f"- *Graph:* linear chain `skill[0] -> ... -> skill[n-1]` in sorted skill_id order (ablation control, not curriculum truth).",
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
        traceback.print_exc()
        raise RuntimeError(
            "run_investor_ablation_real() returned None. "
            "This triggers the stub writer path in main(). "
            "Likely causes: missing/invalid Gate A item params, bank too small (<20), or too few selected skills (<2)."
        )
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
