"""MAP — Charting Student Math Misunderstandings (Kaggle, 2025) loader.

~15 questions × ~52k student free-text explanations with category +
misconception labels. v1 loader only; parked for v2 detector training.

Expected columns:
    row_id, QuestionId, QuestionText, MC_Answer, StudentExplanation,
    Category, Misconception

`Misconception` uses the sentinel 'NA' for rows without a tag; it is
normalised to pandas NA on load.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


_REQUIRED_COLUMNS = (
    "row_id",
    "QuestionId",
    "QuestionText",
    "MC_Answer",
    "StudentExplanation",
    "Category",
    "Misconception",
)


def _require_columns(df: pd.DataFrame, cols: tuple[str, ...]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"MAP CSV missing required columns: {missing}")


def load_explanations(path: Path | str) -> pd.DataFrame:
    """Parse the MAP explanations CSV.

    Returns one row per student explanation with the expected columns.
    `Misconception == 'NA'` (the MAP sentinel for untagged rows) is
    converted to pandas NA.
    """
    df = pd.read_csv(path, low_memory=False)
    _require_columns(df, _REQUIRED_COLUMNS)

    df = df[list(_REQUIRED_COLUMNS)].copy()
    df["Misconception"] = df["Misconception"].replace({"NA": pd.NA})
    return df.reset_index(drop=True)


def cache_processed(explanations_df: pd.DataFrame, out_path: Path | str) -> Path:
    """Write the processed explanations DataFrame to parquet."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    explanations_df.to_parquet(out_path, index=False)
    return out_path


def load_processed(path: Path | str) -> pd.DataFrame:
    """Read a cached parquet produced by `cache_processed`."""
    return pd.read_parquet(path)
