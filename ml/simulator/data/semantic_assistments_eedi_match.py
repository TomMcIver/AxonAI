"""ASSISTments ↔ Eedi 2024 semantic match via sentence-transformers.

Embeds each unique ASSISTments item text and each Eedi question, then for
each ASSISTments item keeps the top-k Eedi questions by cosine similarity
(L2-normalized dot product), filters to similarity > ``--min-sim``, and
writes a CSV of candidate alignments.

Requires optional deps: ``pip install -e '.[semantic-match]'`` (or
``simulator`` + ``sentence-transformers``).

Default inputs mirror other calibration entrypoints: ASSISTments 2012-2013
release CSV and Eedi ``train.csv`` (local path, ``s3://key``, or
``s3://prefix/`` for the Kaggle folder).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from ml.simulator.data.eedi_misconceptions_loader import load as load_eedi
from ml.simulator.data.s3_io import is_s3_uri, materialise

# Reuse the same case-folding and aliases as `assistments_loader` so
# `problem` / `Problem` map the same way when present.
from ml.simulator.data.assistments_loader import _ALIASES, _canonicalise_columns

_ID_CANDIDATES: tuple[str, ...] = (
    "problem_id",
    "problem",
    "item_id",
    "question_id",
)

def _header_to_canonical(name: str) -> str:
    low = name.strip().lower()
    return str(_ALIASES.get(low, low))


def _raw_header_to_canonical_map(
    raw_columns: Sequence[str],
) -> dict[str, str]:
    out: dict[str, str] = {str(c): _header_to_canonical(str(c)) for c in raw_columns}
    seen: dict[str, str] = {}
    for o, n in out.items():
        if n in seen:
            raise ValueError(
                f"Two header columns map to the same name {n!r}: {seen[n]!r} and {o!r}."
            )
        seen[n] = o
    return out


def _resolve_id_column(columns: Sequence[str]) -> str:
    low = {c.lower().strip(): c for c in columns}
    for c in _ID_CANDIDATES:
        if c in low:
            return str(low[c])
    raise KeyError(
        f"Could not find an id column in {_ID_CANDIDATES!r}. "
        f"Columns: {sorted(columns)}"
    )


def _resolve_user_header(name: str, canonical_columns: Sequence[str]) -> str:
    """Map user-facing column name to the canonical name in the file."""
    want = _header_to_canonical(name)
    for c in canonical_columns:
        if c == want or c == name:
            return str(c)
    low = {c.lower().strip(): c for c in canonical_columns}
    if want in low:
        return str(low[want])
    raise KeyError(
        f"Column {name!r} (canonical {want!r}) not found. "
        f"Columns: {sorted(canonical_columns)}"
    )


def _text_column_score(name: str) -> int:
    """Higher = more likely the item body / question stem (ASSISTments)."""
    n = name.lower().strip()
    if n.endswith("_id") or n in ("id", "user_id", "user"):
        return -1
    if n in ("username", "assignment", "log") or "user_id" in n:
        return -1
    if "question_text" in n or n in ("questiontext", "item_text", "problem_text"):
        return 200
    if n in ("template",) or "template" in n:
        return 90
    if n in ("body", "content") or "body" in n or "content" in n:
        return 80
    if n == "name" or n.endswith(".name") or n == "problem_name":
        return 25
    if "question" in n and "id" not in n:
        return 50
    if n == "text" or n.endswith("_text"):
        return 30
    return 0


def _detect_text_column(
    columns: Sequence[str], explicit: str | None
) -> str:
    if explicit is not None:
        return _resolve_user_header(explicit, list(columns))
    best: str | None = None
    best_s = -1
    for c in columns:
        s = _text_column_score(str(c))
        if s > best_s:
            best_s, best = s, str(c)
    # Require a confident hit (not an arbitrary 0-scored field).
    if best is None or best_s < 1:
        raise KeyError(
            "Could not auto-detect an ASSISTments text column. "
            "Pass --assistments-text-column, e.g. the column that holds the "
            f"item stem or body. Columns: {sorted(columns)}"
        )
    return best


def load_unique_assistment_item_texts(
    path: Path | str,
    id_column: str | None = None,
    text_column: str | None = None,
    chunksize: int = 200_000,
) -> pd.DataFrame:
    """Read ASSISTments CSV; one row per unique id with first non-empty text."""
    local = materialise(path) if is_s3_uri(str(path)) else Path(path)
    raw0 = pd.read_csv(
        local,
        nrows=0,
        low_memory=False,
        encoding="utf-8-sig",
        encoding_errors="replace",
    )
    raw_to_canon = _raw_header_to_canonical_map(list(raw0.columns))
    canon_to_raw = {v: k for k, v in raw_to_canon.items()}

    head = _canonicalise_columns(raw0)
    if id_column is None:
        id_key = _resolve_id_column(list(head.columns))
    else:
        id_key = _resolve_user_header(id_column, list(head.columns))
    text_key = _detect_text_column(list(head.columns), text_column)

    orig_id = canon_to_raw[id_key]
    orig_text = canon_to_raw[text_key]
    usecols: list[str] = [str(orig_id), str(orig_text)]

    first: dict[str, str] = {}
    for chunk in pd.read_csv(
        local,
        usecols=usecols,
        chunksize=chunksize,
        low_memory=False,
        encoding="utf-8-sig",
        encoding_errors="replace",
    ):
        chunk = _canonicalise_columns(chunk)
        chunk = chunk.dropna(subset=[id_key])
        chunk[id_key] = chunk[id_key].astype(str).str.strip()
        chunk[text_key] = chunk[text_key].apply(
            lambda x: ("" if pd.isna(x) else str(x).strip())
        )
        chunk = chunk[chunk[id_key] != ""]  # type: ignore[unreachable]
        for pid, text in zip(
            chunk[id_key], chunk[text_key], strict=True
        ):
            if pid in first or not text or text.lower() in ("nan", "none"):
                continue
            first[pid] = text
    if not first:
        raise ValueError("No non-empty (id, text) pairs found in ASSISTments file.")

    out = pd.DataFrame(
        {
            "assistments_item_id": list(first.keys()),
            "assistments_text": list(first.values()),
        }
    )
    return out


def load_eedi_unique_question_texts(questions_path: Path | str) -> pd.DataFrame:
    """QuestionId (string) and QuestionText from the Eedi loader."""
    eedi = load_eedi(questions_path)
    q = eedi.questions_df[["QuestionId", "QuestionText"]].copy()
    q = q.dropna(subset=["QuestionId"])
    q["QuestionId"] = q["QuestionId"].astype(str).str.strip()
    q["QuestionText"] = q["QuestionText"].apply(
        lambda x: ("" if pd.isna(x) else str(x).strip())
    )
    q = q[(q["QuestionId"] != "") & (q["QuestionText"] != "")]
    q = q.drop_duplicates(subset=["QuestionId"], keep="first")
    return q.rename(
        columns={"QuestionId": "eedi_question_id", "QuestionText": "eedi_text"}
    )


def _topk_cosine(
    a_norm: np.ndarray, e_norm: np.ndarray, top_k: int
) -> tuple[np.ndarray, np.ndarray]:
    """Cosine sim for L2-normalized rows: a @ e.T, top-k per row of a."""
    try:
        import torch
    except ImportError as e:
        raise ImportError(
            "semantic matching needs PyTorch (installed with sentence-transformers)."
        ) from e
    m = e_norm.shape[0]
    k = min(top_k, m)
    if k < 1:
        raise ValueError("No Eedi questions to match against.")
    a_t = torch.from_numpy(a_norm)
    e_t = torch.from_numpy(e_norm)
    # (n, d) @ (d, m) -> (n, m)
    sim = a_t @ e_t.T
    return torch.topk(sim, k=k, dim=1, largest=True)  # type: ignore[no-any-return]


def run(
    assistments_path: Path | str,
    eedi_questions_path: Path | str,
    out_csv: Path | str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    min_sim: float = 0.75,
    top_k: int = 3,
    encode_batch_size: int = 64,
    assistments_id_column: str | None = None,
    assistments_text_column: str | None = None,
) -> Path:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "Install sentence-transformers: pip install 'sentence-transformers>=3.0' "
            "or: pip install -e '.[semantic-match]'"
        ) from e

    a_df = load_unique_assistment_item_texts(
        assistments_path,
        id_column=assistments_id_column,
        text_column=assistments_text_column,
    )
    e_df = load_eedi_unique_question_texts(eedi_questions_path)
    a_texts = a_df["assistments_text"].tolist()
    e_texts = e_df["eedi_text"].tolist()
    a_ids = a_df["assistments_item_id"].astype(str).tolist()
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
    vals_t, inds_t = _topk_cosine(np.asarray(a_vec, dtype=np.float32), np.asarray(e_vec, dtype=np.float32), top_k)
    scores = vals_t.cpu().numpy()
    indices = inds_t.cpu().numpy()

    rows: list[dict[str, str | float]] = []
    for i in range(len(a_ids)):
        for t in range(scores.shape[1]):
            s = float(scores[i, t])
            if s <= min_sim:
                continue
            j = int(indices[i, t])
            rows.append(
                {
                    "assistments_item_id": a_ids[i],
                    "eedi_question_id": e_ids[j],
                    "similarity_score": s,
                    "assistments_text": a_texts[i],
                    "eedi_text": e_texts[j],
                }
            )
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(rows)
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Semantic ASSISTments to Eedi 2024 candidate matches (top-k, cosine)."
    )
    p.add_argument(
        "--assistments",
        type=str,
        default="s3://axonai-datasets-924300129944/assistments/2012-2013-data-with-predictions-4-final.csv",
        help="ASSISTments item/responses CSV (path or s3:// URI to a .csv).",
    )
    p.add_argument(
        "--eedi-questions",
        type=str,
        default="s3://axonai-datasets-924300129944/eedi_mining_misconceptions/",
        help="Eedi questions: train.csv path, or s3://.../ folder prefix (Kaggle layout).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/assistments_eedi_candidate_matches.csv"),
        help="Output CSV path.",
    )
    p.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model id (HuggingFace).",
    )
    p.add_argument(
        "--min-sim",
        type=float,
        default=0.75,
        help="Keep pairs with similarity strictly above this (cosine, post top-k).",
    )
    p.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of nearest Eedi questions per ASSISTments item.",
    )
    p.add_argument(
        "--encode-batch-size",
        type=int,
        default=64,
        help="encode() batch size.",
    )
    p.add_argument(
        "--assistments-id-column",
        type=str,
        default=None,
        help="Override id column (after the same header normalization as assistments_loader).",
    )
    p.add_argument(
        "--assistments-text-column",
        type=str,
        default=None,
        help="Column holding item / question text (auto-detect if omitted).",
    )
    args = p.parse_args(argv)
    out = run(
        assistments_path=args.assistments,
        eedi_questions_path=args.eedi_questions,
        out_csv=args.out,
        model_name=args.model,
        min_sim=args.min_sim,
        top_k=args.top_k,
        encode_batch_size=args.encode_batch_size,
        assistments_id_column=args.assistments_id_column,
        assistments_text_column=args.assistments_text_column,
    )
    print(f"Wrote {out} ({Path(out).stat().st_size} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
