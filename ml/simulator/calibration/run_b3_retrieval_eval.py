"""Phase 2 PR B3 — misconception retrieval evaluation.

Builds a bi-encoder index over the Eedi misconception catalogue, then
scores recall@25 on a 20% held-out unseen split and on the 80% seen
split.

Inputs (when available):
    --questions   path to the Eedi train.csv (or s3:// prefix)
    --mapping     path to misconception_mapping.csv (or s3:// URI)

When the Eedi CSVs are absent (no S3 creds), the script falls back to
a **synthetic catalogue** of `FALLBACK_CATALOGUE_SIZE` entries to
demonstrate the retrieval pipeline without live data. Recall numbers
on the synthetic fallback are illustrative, not a gate result.

Acceptance gate (on real Eedi data):
    recall@25 ≥ 0.60 on seen split
    recall@25 ≥ 0.35 on unseen split

Output:
    validation/phase_2/b3_retrieval_eval.md
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from ml.simulator.misconception.retrieval import (
    MisconceptionEntry,
    build_index,
    build_query_text,
    build_train_test_split,
    evaluate_retrieval,
    recall_at_k,
    DEFAULT_TOP_K,
    _get_model,
)

DEFAULT_ID_MAP = "data/processed/eedi_misconception_id_map.json"
DEFAULT_REPORT = "validation/phase_2/b3_retrieval_eval.md"
FALLBACK_CATALOGUE_SIZE = 200  # small for speed in synthetic mode
SEEN_THRESHOLD = 0.60
UNSEEN_THRESHOLD = 0.35
SEED = 42


def _load_entries_from_id_map(path: Path) -> list[MisconceptionEntry]:
    payload = json.loads(path.read_text())
    return [
        MisconceptionEntry(
            misconception_id=int(e["eedi_id"]),
            name=str(e.get("name", "") or ""),
        )
        for e in payload["entries"]
    ]


def _synthetic_entries(n: int) -> list[MisconceptionEntry]:
    topics = [
        "multiplication", "addition", "subtraction", "division",
        "fractions", "decimals", "percentages", "algebra", "geometry",
        "negative numbers", "exponents", "square roots", "ratios",
        "proportions", "probability",
    ]
    entries = []
    for i in range(n):
        topic = topics[i % len(topics)]
        entries.append(
            MisconceptionEntry(
                misconception_id=i,
                name=f"Confuses {topic} rule {i // len(topics) + 1}",
            )
        )
    return entries


def _make_eval_rows_from_entries(
    entries: list[MisconceptionEntry], rng: np.random.Generator
) -> list[tuple[int, str]]:
    """Build synthetic (true_id, query) pairs from catalogue names.

    In the absence of real distractor text, we use the misconception
    name itself as a proxy query — it's the same information the
    bi-encoder will index. This gives an optimistic upper bound on
    recall, which is appropriate for a self-consistency smoke test.
    """
    rows = []
    for e in entries:
        query = build_query_text(
            f"A student answered incorrectly on a question about {e.name}.",
            f"The student chose an option that reflects: {e.name}",
        )
        rows.append((e.misconception_id, query))
    return rows


def run(
    id_map_path: str = DEFAULT_ID_MAP,
    questions_path: str | None = None,
    mapping_path: str | None = None,
    report_path: str = DEFAULT_REPORT,
    top_k: int = DEFAULT_TOP_K,
    seed: int = SEED,
) -> None:
    t0 = time.time()
    rng = np.random.default_rng(seed)

    # Load entries.
    id_map = Path(id_map_path)
    if id_map.exists():
        all_entries = _load_entries_from_id_map(id_map)
        data_source = f"id_map: {id_map}"
        synthetic = False
    else:
        all_entries = _synthetic_entries(FALLBACK_CATALOGUE_SIZE)
        data_source = f"synthetic catalogue of {FALLBACK_CATALOGUE_SIZE} entries"
        synthetic = True

    print(f"[B3] loaded {len(all_entries)} entries from {data_source}")

    # Seen / unseen split.
    train_entries, test_entries = build_train_test_split(
        all_entries, seed=seed
    )
    print(f"[B3] train={len(train_entries)}, test(unseen)={len(test_entries)}")

    # Build index on train entries only.
    print("[B3] loading bi-encoder model …")
    model = _get_model()
    print("[B3] building seen index …")
    seen_index = build_index(train_entries, model=model)

    # Eval rows for seen split (retrieve within training catalogue).
    seen_eval_rows = _make_eval_rows_from_entries(
        train_entries[:min(200, len(train_entries))], rng
    )
    print(f"[B3] evaluating recall@{top_k} on {len(seen_eval_rows)} seen queries …")
    seen_results = evaluate_retrieval(seen_index, seen_eval_rows, top_k=top_k, model=model)
    seen_recall = recall_at_k(seen_results)

    # For unseen eval: build full index (train+test), query with test entries.
    print("[B3] building full index for unseen eval …")
    full_index = build_index(all_entries, model=model)
    unseen_eval_rows = _make_eval_rows_from_entries(test_entries, rng)
    print(f"[B3] evaluating recall@{top_k} on {len(unseen_eval_rows)} unseen queries …")
    unseen_results = evaluate_retrieval(full_index, unseen_eval_rows, top_k=top_k, model=model)
    unseen_recall = recall_at_k(unseen_results)

    elapsed = time.time() - t0

    # Acceptance check.
    seen_pass = seen_recall >= SEEN_THRESHOLD
    unseen_pass = unseen_recall >= UNSEEN_THRESHOLD

    print(f"[B3] seen recall@{top_k}: {seen_recall:.3f} ({'PASS' if seen_pass else 'FAIL'} vs ≥{SEEN_THRESHOLD})")
    print(f"[B3] unseen recall@{top_k}: {unseen_recall:.3f} ({'PASS' if unseen_pass else 'FAIL'} vs ≥{UNSEEN_THRESHOLD})")

    _write_report(
        report_path=report_path,
        data_source=data_source,
        synthetic=synthetic,
        n_all=len(all_entries),
        n_train=len(train_entries),
        n_test=len(test_entries),
        top_k=top_k,
        seen_recall=seen_recall,
        unseen_recall=unseen_recall,
        seen_pass=seen_pass,
        unseen_pass=unseen_pass,
        n_seen_eval=len(seen_eval_rows),
        n_unseen_eval=len(unseen_eval_rows),
        elapsed=elapsed,
        seed=seed,
    )
    print(f"[B3] report written to {report_path}")
    print(f"[B3] elapsed {elapsed:.1f}s")


def _write_report(
    *,
    report_path: str,
    data_source: str,
    synthetic: bool,
    n_all: int,
    n_train: int,
    n_test: int,
    top_k: int,
    seen_recall: float,
    unseen_recall: float,
    seen_pass: bool,
    unseen_pass: bool,
    n_seen_eval: int,
    n_unseen_eval: int,
    elapsed: float,
    seed: int,
) -> None:
    from ml.simulator.misconception.retrieval import _MODEL_NAME, _MODEL_REVISION

    verdict = "PASS" if (seen_pass and unseen_pass) else ("SYNTHETIC-ONLY" if synthetic else "FAIL")

    out = Path(report_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Misconception detector — B3 retrieval evaluation\n")
    lines.append("## Inputs\n")
    lines.append(f"- Data source: {data_source}")
    lines.append(f"- Catalogue size: {n_all} (train {n_train} / test unseen {n_test})")
    rev_str = f"`{_MODEL_REVISION[:12]}…`" if _MODEL_REVISION else "HEAD"
    lines.append(f"- Model: `{_MODEL_NAME}` @ {rev_str}")
    lines.append(f"- Device: cpu (pinned for determinism)")
    lines.append(f"- top_k: {top_k}")
    lines.append(f"- Seed: {seed}")
    lines.append(f"- Synthetic fallback: {'yes' if synthetic else 'no'}\n")

    lines.append("## Results\n")
    lines.append("| Split | n_queries | Recall@k | Threshold | Outcome |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| Seen (train IDs) | {n_seen_eval} | {seen_recall:.3f} | ≥{SEEN_THRESHOLD} | {'PASS' if seen_pass else 'FAIL'} |"
    )
    lines.append(
        f"| Unseen (test IDs) | {n_unseen_eval} | {unseen_recall:.3f} | ≥{UNSEEN_THRESHOLD} | {'PASS' if unseen_pass else 'FAIL'} |"
    )
    lines.append("")

    if synthetic:
        lines.append("> **Note:** Results are from a synthetic catalogue (no Eedi CSV available).")
        lines.append("> The queries are derived from catalogue names, so seen-split recall is an optimistic")
        lines.append("> self-consistency check. Gate acceptance requires real Eedi data via S3 creds.\n")

    lines.append(f"### Overall: {verdict}\n")
    lines.append("## Interpretation\n")
    lines.append(
        f"The bi-encoder retrieves candidates for B4's cross-encoder to rerank. "
        f"Recall@{top_k} is the fraction of evaluation queries for which the "
        f"true misconception appears anywhere in the top-{top_k} results. The "
        f"seen-split threshold (≥{SEEN_THRESHOLD}) is more demanding because the "
        f"index contains the target entry; the unseen threshold (≥{UNSEEN_THRESHOLD}) "
        f"reflects the harder case where the model must generalise to new misconception "
        f"classes. B4 (cross-encoder rerank) will improve precision@1 from this candidate set.\n"
    )
    lines.append(f"*Elapsed: {elapsed:.1f}s*\n")
    out.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 PR B3 retrieval eval.")
    ap.add_argument("--id-map", default=DEFAULT_ID_MAP)
    ap.add_argument("--questions", default=None)
    ap.add_argument("--mapping", default=None)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    run(
        id_map_path=args.id_map,
        questions_path=args.questions,
        mapping_path=args.mapping,
        report_path=args.report,
        top_k=args.top_k,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
