"""Semantic Gate A (problem_id) ↔ Eedi QuestionId crosswalk builder.

This avoids ASSISTments `problem_log_id` namespace issues by matching in the
same id space used by Gate A calibration:

    Gate A `real_item_params.parquet`.`item_id`  <->  ASSISTments `problem_id`

Pipeline:
1) Load Gate A item params (`item_id`, `a`, `b` required)
2) Load ASSISTments raw CSV (local or s3://) and derive one text per `problem_id`
3) Keep only rows where `problem_id` is in Gate A `item_id`
4) Load Eedi questions (`QuestionId`, `QuestionText`)
5) Embed both text sets with `all-MiniLM-L6-v2`
6) Emit semantic top-k matches above threshold

Output columns:
    assistments_problem_id, eedi_question_id, similarity_score,
    assistments_text, eedi_text
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from ml.simulator.data.assistments_loader import _canonicalise_columns
from ml.simulator.data.eedi_misconceptions_loader import load as load_eedi
from ml.simulator.data.s3_io import is_s3_uri, materialise

REPO = Path(__file__).resolve().parents[3]
DEFAULT_GATE_A = REPO / "data" / "processed" / "real_item_params.parquet"
DEFAULT_OUT = REPO / "data" / "processed" / "gate_a_eedi_verified_crosswalk.csv"
DEFAULT_ASSIST = (
    "s3://axonai-datasets-924300129944/assistments/"
    "2012-2013-data-with-predictions-4-final.csv"
)
DEFAULT_EEDI = "s3://axonai-datasets-924300129944/eedi_mining_misconceptions/"


def _text_column_score(name: str) -> int:
    n = name.lower().strip()
    if n == "problem_id" or n.endswith("_id"):
        return -1
    if "questiontext" in n or "question_text" in n:
        return 250
    if n in ("original_answer", "problem_text", "item_text"):
        return 200
    if "template" in n:
        return 120
    if "answer" in n or "text" in n:
        return 80
    if n in ("problem", "question", "body", "content"):
        return 60
    return 0


def _select_text_columns(columns: Sequence[str]) -> list[str]:
    scored = sorted(
        ((c, _text_column_score(c)) for c in columns),
        key=lambda x: x[1],
        reverse=True,
    )
    out: list[str] = [c for c, s in scored if s > 0]
    return out


def _first_nonempty_text(row: pd.Series, cols: Sequence[str]) -> str:
    for c in cols:
        if c not in row.index:
            continue
        v = row[c]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if not s or s.lower() in ("nan", "none"):
            continue
        return s
    return ""


def _load_gate_a_item_ids(path: Path) -> set[int]:
    df = pd.read_parquet(path)
    needed = {"item_id", "a", "b"}
    missing = needed - set(df.columns)
    if missing:
        raise KeyError(f"Gate A item params missing required columns: {missing}")
    return set(pd.to_numeric(df["item_id"], errors="coerce").dropna().astype(int))


def _load_assist_problem_texts(
    assistments_path: str | Path,
    gate_item_ids: set[int],
    chunksize: int = 200_000,
    text_column: str | None = None,
) -> pd.DataFrame:
    local = materialise(assistments_path) if is_s3_uri(str(assistments_path)) else Path(assistments_path)
    raw0 = pd.read_csv(local, nrows=0, low_memory=False, encoding="utf-8-sig", encoding_errors="replace")
    head = _canonicalise_columns(raw0)
    if "problem_id" not in head.columns:
        raise KeyError(f"ASSISTments file missing `problem_id`. Columns: {list(head.columns)}")

    if text_column is not None:
        text_candidates = [text_column.strip().lower()]
        if text_candidates[0] not in head.columns:
            raise KeyError(
                f"text column {text_column!r} not found after normalization; columns: {list(head.columns)}"
            )
    else:
        text_candidates = _select_text_columns(list(head.columns))
    if not text_candidates:
        raise KeyError(
            "Could not auto-detect a suitable ASSISTments text column. "
            "Pass --assistments-text-column."
        )

    usecols = [c for c in ["problem_id", *text_candidates] if c in head.columns]
    first_text: dict[int, str] = {}
    for chunk in pd.read_csv(
        local,
        usecols=usecols,
        chunksize=chunksize,
        low_memory=False,
        encoding="utf-8-sig",
        encoding_errors="replace",
    ):
        chunk = _canonicalise_columns(chunk)
        chunk["problem_id"] = pd.to_numeric(chunk["problem_id"], errors="coerce")
        chunk = chunk.dropna(subset=["problem_id"])
        chunk["problem_id"] = chunk["problem_id"].astype(int)
        chunk = chunk[chunk["problem_id"].isin(gate_item_ids)]
        if chunk.empty:
            continue
        for _, row in chunk.iterrows():
            pid = int(row["problem_id"])
            if pid in first_text:
                continue
            txt = _first_nonempty_text(row, text_candidates)
            if txt:
                first_text[pid] = txt
    if not first_text:
        raise ValueError("No Gate A problem texts found in ASSISTments source.")
    return pd.DataFrame(
        {
            "assistments_problem_id": list(first_text.keys()),
            "assistments_text": list(first_text.values()),
        }
    )


def _load_eedi_question_texts(questions_path: str | Path) -> pd.DataFrame:
    eedi = load_eedi(questions_path=questions_path)
    q = eedi.questions_df[["QuestionId", "QuestionText"]].copy()
    q = q.dropna(subset=["QuestionId"])
    q["QuestionId"] = q["QuestionId"].astype(str).str.strip()
    q["QuestionText"] = q["QuestionText"].fillna("").astype(str).str.strip()
    q = q[(q["QuestionId"] != "") & (q["QuestionText"] != "")]
    q = q.drop_duplicates(subset=["QuestionId"], keep="first")
    return q.rename(columns={"QuestionId": "eedi_question_id", "QuestionText": "eedi_text"})


def _topk_cosine(
    a_norm: np.ndarray, e_norm: np.ndarray, top_k: int
) -> tuple[np.ndarray, np.ndarray]:
    import torch

    m = e_norm.shape[0]
    k = min(top_k, m)
    if k < 1:
        raise ValueError("No Eedi questions available.")
    a_t = torch.from_numpy(a_norm)
    e_t = torch.from_numpy(e_norm)
    sim = a_t @ e_t.T
    vals, inds = torch.topk(sim, k=k, dim=1, largest=True)
    return vals.cpu().numpy(), inds.cpu().numpy()


def run(
    item_params_path: Path = DEFAULT_GATE_A,
    assistments_path: str = DEFAULT_ASSIST,
    eedi_questions_path: str = DEFAULT_EEDI,
    out_csv: Path = DEFAULT_OUT,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    min_sim: float = 0.70,
    top_k: int = 3,
    encode_batch_size: int = 64,
    assistments_text_column: str | None = None,
) -> Path:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "Install sentence-transformers: pip install 'sentence-transformers>=3.0'"
        ) from e

    gate_item_ids = _load_gate_a_item_ids(item_params_path)
    print(f"[gate_a_match] Gate A item_ids: {len(gate_item_ids)}")
    a_df = _load_assist_problem_texts(
        assistments_path=assistments_path,
        gate_item_ids=gate_item_ids,
        text_column=assistments_text_column,
    )
    print(f"[gate_a_match] ASSISTments Gate-A texts found: {len(a_df)}")
    e_df = _load_eedi_question_texts(questions_path=eedi_questions_path)
    print(f"[gate_a_match] Eedi question texts: {len(e_df)}")

    a_texts = a_df["assistments_text"].astype(str).tolist()
    e_texts = e_df["eedi_text"].astype(str).tolist()
    a_ids = a_df["assistments_problem_id"].astype(int).tolist()
    e_ids = e_df["eedi_question_id"].astype(str).tolist()

    model = SentenceTransformer(model_name)
    a_vec = model.encode(
        a_texts,
        batch_size=encode_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    e_vec = model.encode(
        e_texts,
        batch_size=encode_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    vals, inds = _topk_cosine(
        np.asarray(a_vec, dtype=np.float32),
        np.asarray(e_vec, dtype=np.float32),
        top_k=top_k,
    )

    rows: list[dict[str, str | float | int]] = []
    for i in range(len(a_ids)):
        for j in range(vals.shape[1]):
            sim = float(vals[i, j])
            if sim <= min_sim:
                continue
            e_idx = int(inds[i, j])
            rows.append(
                {
                    "assistments_problem_id": int(a_ids[i]),
                    "eedi_question_id": int(float(e_ids[e_idx])),
                    "similarity_score": sim,
                    "assistments_text": a_texts[i],
                    "eedi_text": e_texts[e_idx],
                }
            )
    out_df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[gate_a_match] wrote {out_csv} ({len(out_df)} rows)")
    return out_csv


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Build Gate A namespace semantic crosswalk to Eedi QuestionId."
    )
    p.add_argument("--item-params", type=Path, default=DEFAULT_GATE_A)
    p.add_argument("--assistments", type=str, default=DEFAULT_ASSIST)
    p.add_argument("--eedi-questions", type=str, default=DEFAULT_EEDI)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
    )
    p.add_argument("--min-sim", type=float, default=0.70)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--encode-batch-size", type=int, default=64)
    p.add_argument("--assistments-text-column", type=str, default=None)
    args = p.parse_args(argv)
    run(
        item_params_path=args.item_params,
        assistments_path=args.assistments,
        eedi_questions_path=args.eedi_questions,
        out_csv=args.out,
        model_name=args.model,
        min_sim=args.min_sim,
        top_k=args.top_k,
        encode_batch_size=args.encode_batch_size,
        assistments_text_column=args.assistments_text_column,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
