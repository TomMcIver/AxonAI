"""Phase 2 PR B4 — cross-encoder rerank evaluation.

Takes the B3 retrieval index, runs the cross-encoder reranker on top,
reports precision@1 and MRR on the seen and unseen splits.

Acceptance gate:
    precision@1 ≥ 0.50 on seen split

Falls back to a 200-entry synthetic catalogue when no Eedi CSV is
available (same pattern as run_b3_retrieval_eval.py).

Output:
    validation/phase_2/b4_rerank_eval.md
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
    _get_model as _get_bi_model,
    DEFAULT_TOP_K,
)
from ml.simulator.misconception.reranker import (
    evaluate_rerank,
    rerank,
    _get_ce_model,
)

DEFAULT_REPORT = "validation/phase_2/b4_rerank_eval.md"
DEFAULT_ID_MAP = "data/processed/eedi_misconception_id_map.json"
FALLBACK_CATALOGUE_SIZE = 200
SEEN_P1_THRESHOLD = 0.50
SEED = 42


def _load_entries(id_map_path: Path) -> tuple[list[MisconceptionEntry], str, bool]:
    if id_map_path.exists():
        payload = json.loads(id_map_path.read_text())
        entries = [
            MisconceptionEntry(int(e["eedi_id"]), str(e.get("name", "") or ""))
            for e in payload["entries"]
        ]
        return entries, f"id_map: {id_map_path}", False
    topics = [
        "multiplication", "addition", "subtraction", "division", "fractions",
        "decimals", "percentages", "algebra", "geometry", "negative numbers",
        "exponents", "square roots", "ratios", "proportions", "probability",
    ]
    entries = [
        MisconceptionEntry(i, f"Confuses {topics[i % len(topics)]} rule {i // len(topics) + 1}")
        for i in range(FALLBACK_CATALOGUE_SIZE)
    ]
    return entries, f"synthetic catalogue of {FALLBACK_CATALOGUE_SIZE} entries", True


def _make_eval_rows(entries: list[MisconceptionEntry]) -> list[tuple[int, str]]:
    return [
        (
            e.misconception_id,
            build_query_text(
                f"A student answered incorrectly on a question about {e.name}.",
                f"The student chose an option reflecting: {e.name}",
            ),
        )
        for e in entries
    ]


def run(
    id_map_path: str = DEFAULT_ID_MAP,
    report_path: str = DEFAULT_REPORT,
    top_k: int = DEFAULT_TOP_K,
    seed: int = SEED,
) -> None:
    t0 = time.time()
    all_entries, data_source, synthetic = _load_entries(Path(id_map_path))
    print(f"[B4] loaded {len(all_entries)} entries from {data_source}")

    train_entries, test_entries = build_train_test_split(all_entries, seed=seed)
    print(f"[B4] train={len(train_entries)}, test={len(test_entries)}")

    print("[B4] loading bi-encoder …")
    bi_model = _get_bi_model()
    print("[B4] loading cross-encoder …")
    ce_model = _get_ce_model()

    seen_index = build_index(train_entries, model=bi_model)
    full_index = build_index(all_entries, model=bi_model)

    seen_eval = _make_eval_rows(train_entries[:min(100, len(train_entries))])
    unseen_eval = _make_eval_rows(test_entries)

    # Seen split.
    print(f"[B4] reranking {len(seen_eval)} seen queries …")
    seen_reranked = []
    for true_id, query in seen_eval:
        candidates = evaluate_retrieval(seen_index, [(true_id, query)], top_k=top_k, model=bi_model)
        bi_candidates = [(c.true_misconception_id, query, c.retrieved_ids) for c in candidates]
        # Retrieve as (entry, score) pairs for reranker.
        from ml.simulator.misconception.retrieval import retrieve
        raw = retrieve(seen_index, query, top_k=top_k, model=bi_model)
        reranked = rerank(query, raw, model=ce_model)
        seen_reranked.append((true_id, reranked))

    seen_metrics = evaluate_rerank(seen_reranked)
    seen_pass = seen_metrics["precision_at_1"] >= SEEN_P1_THRESHOLD

    # Unseen split.
    print(f"[B4] reranking {len(unseen_eval)} unseen queries …")
    unseen_reranked = []
    for true_id, query in unseen_eval:
        from ml.simulator.misconception.retrieval import retrieve
        raw = retrieve(full_index, query, top_k=top_k, model=bi_model)
        reranked = rerank(query, raw, model=ce_model)
        unseen_reranked.append((true_id, reranked))

    unseen_metrics = evaluate_rerank(unseen_reranked)

    elapsed = time.time() - t0
    verdict = "PASS" if seen_pass else ("SYNTHETIC-ONLY" if synthetic else "FAIL")

    print(f"[B4] seen P@1={seen_metrics['precision_at_1']:.3f} MRR={seen_metrics['mrr']:.3f} ({'PASS' if seen_pass else 'FAIL'})")
    print(f"[B4] unseen P@1={unseen_metrics['precision_at_1']:.3f} MRR={unseen_metrics['mrr']:.3f}")
    print(f"[B4] overall: {verdict}")

    _write_report(
        report_path=report_path,
        data_source=data_source,
        synthetic=synthetic,
        seen_metrics=seen_metrics,
        unseen_metrics=unseen_metrics,
        seen_pass=seen_pass,
        top_k=top_k,
        elapsed=elapsed,
    )
    print(f"[B4] report written to {report_path}")


def _write_report(
    *,
    report_path: str,
    data_source: str,
    synthetic: bool,
    seen_metrics: dict,
    unseen_metrics: dict,
    seen_pass: bool,
    top_k: int,
    elapsed: float,
) -> None:
    from ml.simulator.misconception.reranker import _CE_MODEL_NAME

    out = Path(report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Misconception detector — B4 rerank evaluation\n")
    lines.append("## Inputs\n")
    lines.append(f"- Data source: {data_source}")
    lines.append(f"- Cross-encoder model: `{_CE_MODEL_NAME}` (CPU-pinned)")
    lines.append(f"- Retrieved top_k for reranking: {top_k}")
    lines.append(f"- Synthetic fallback: {'yes' if synthetic else 'no'}\n")
    lines.append("## Results\n")
    lines.append("| Split | P@1 | MRR | n_queries | P@1 gate |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| Seen | {seen_metrics['precision_at_1']:.3f} | {seen_metrics['mrr']:.3f} "
        f"| {seen_metrics['n_queries']} | {'PASS' if seen_pass else 'FAIL'} (≥{SEEN_P1_THRESHOLD}) |"
    )
    lines.append(
        f"| Unseen | {unseen_metrics['precision_at_1']:.3f} | {unseen_metrics['mrr']:.3f} "
        f"| {unseen_metrics['n_queries']} | — |"
    )
    lines.append("")
    if synthetic:
        lines.append(
            "> **Note:** Results from synthetic catalogue (self-consistency check). "
            "Gate acceptance requires real Eedi S3 data.\n"
        )
    lines.append(f"### Overall: {'PASS' if seen_pass else ('SYNTHETIC-ONLY' if synthetic else 'FAIL')}\n")
    lines.append(f"*Elapsed: {elapsed:.1f}s*\n")
    out.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 PR B4 rerank eval.")
    ap.add_argument("--id-map", default=DEFAULT_ID_MAP)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    run(id_map_path=args.id_map, report_path=args.report, top_k=args.top_k, seed=args.seed)


if __name__ == "__main__":
    main()
