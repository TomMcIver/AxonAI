"""Eedi 2024 — Mining Misconceptions in Mathematics loader.

Provides question-level metadata + distractor→misconception mapping.
**Not** response data. Used in v1 as:
    - misconception taxonomy
    - item-bank distractor metadata (stored but unused by v1 response
      model; v2 weights distractor selection by susceptibility)

Expected columns on the main questions CSV:
    QuestionId, ConstructId, ConstructName, SubjectId, SubjectName,
    CorrectAnswer, QuestionText,
    AnswerAText, AnswerBText, AnswerCText, AnswerDText,
    MisconceptionAId, MisconceptionBId, MisconceptionCId, MisconceptionDId

Misconceptions are integer IDs; blank cells for the correct option are
left as NA. The Kaggle release also ships an optional
`misconception_mapping.csv` of the form (MisconceptionId, MisconceptionName)
— if passed, we build the catalogue from it; otherwise we derive IDs
without names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class EediFrames:
    """Tidy views of the Eedi 2024 question metadata."""

    questions_df: pd.DataFrame
    answer_options_df: pd.DataFrame
    distractor_misconception_map_df: pd.DataFrame
    misconception_catalogue_df: pd.DataFrame


_REQUIRED_COLUMNS = (
    "QuestionId",
    "ConstructId",
    "ConstructName",
    "SubjectId",
    "SubjectName",
    "CorrectAnswer",
    "QuestionText",
    "AnswerAText",
    "AnswerBText",
    "AnswerCText",
    "AnswerDText",
)

_OPTIONS = ("A", "B", "C", "D")


def _require_columns(df: pd.DataFrame, cols: tuple[str, ...]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Eedi CSV missing required columns: {missing}")


def load(
    questions_path: Path | str,
    misconception_mapping_path: Optional[Path | str] = None,
) -> EediFrames:
    """Parse the Eedi 2024 question CSV (and optional mapping file)."""
    df = pd.read_csv(questions_path, low_memory=False)
    _require_columns(df, _REQUIRED_COLUMNS)

    questions_df = df[
        [
            "QuestionId",
            "ConstructId",
            "ConstructName",
            "SubjectId",
            "SubjectName",
            "CorrectAnswer",
            "QuestionText",
        ]
    ].copy()

    # Long-form answer options: one row per (QuestionId, Option).
    option_rows = []
    for opt in _OPTIONS:
        text_col = f"Answer{opt}Text"
        option_rows.append(
            pd.DataFrame(
                {
                    "QuestionId": df["QuestionId"],
                    "Option": opt,
                    "Text": df[text_col],
                    "IsCorrect": df["CorrectAnswer"].astype(str).str.strip() == opt,
                }
            )
        )
    answer_options_df = (
        pd.concat(option_rows, ignore_index=True)
        .sort_values(["QuestionId", "Option"])
        .reset_index(drop=True)
    )

    # Distractor → misconception map: only rows where the misconception
    # is populated (blank for the correct answer, blank for distractors
    # the curators didn't tag).
    distractor_rows = []
    for opt in _OPTIONS:
        misc_col = f"Misconception{opt}Id"
        if misc_col not in df.columns:
            continue
        sub = df[["QuestionId", misc_col]].copy()
        sub = sub.rename(columns={misc_col: "MisconceptionId"})
        sub["Option"] = opt
        sub = sub[sub["MisconceptionId"].notna()]
        distractor_rows.append(sub[["QuestionId", "Option", "MisconceptionId"]])
    if distractor_rows:
        distractor_misconception_map_df = (
            pd.concat(distractor_rows, ignore_index=True)
            .astype({"MisconceptionId": "Int64"})
            .sort_values(["QuestionId", "Option"])
            .reset_index(drop=True)
        )
    else:
        distractor_misconception_map_df = pd.DataFrame(
            columns=["QuestionId", "Option", "MisconceptionId"]
        )

    # Catalogue: prefer the shipped mapping file; fall back to the unique
    # IDs seen in this questions CSV with no name.
    if misconception_mapping_path is not None:
        cat = pd.read_csv(misconception_mapping_path)
        cat.columns = [c.strip() for c in cat.columns]
        if {"MisconceptionId", "MisconceptionName"} - set(cat.columns):
            raise KeyError(
                "misconception_mapping.csv must have MisconceptionId + MisconceptionName columns"
            )
        misconception_catalogue_df = cat[["MisconceptionId", "MisconceptionName"]].copy()
    else:
        ids = distractor_misconception_map_df["MisconceptionId"].dropna().unique()
        misconception_catalogue_df = pd.DataFrame(
            {"MisconceptionId": sorted(int(x) for x in ids), "MisconceptionName": ""}
        )

    return EediFrames(
        questions_df=questions_df.reset_index(drop=True),
        answer_options_df=answer_options_df,
        distractor_misconception_map_df=distractor_misconception_map_df,
        misconception_catalogue_df=misconception_catalogue_df,
    )


def cache_processed(frames: EediFrames, out_path: Path | str) -> Path:
    """Write all four frames into a single parquet file with named sheets."""
    # Parquet doesn't have sheets — write the four frames to a directory
    # with predictable filenames. Keeps each frame independently readable.
    out_dir = Path(out_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames.questions_df.to_parquet(out_dir / "questions.parquet", index=False)
    frames.answer_options_df.to_parquet(out_dir / "answer_options.parquet", index=False)
    frames.distractor_misconception_map_df.to_parquet(
        out_dir / "distractor_misconception_map.parquet", index=False
    )
    frames.misconception_catalogue_df.to_parquet(
        out_dir / "misconception_catalogue.parquet", index=False
    )
    return out_dir


def load_processed(in_dir: Path | str) -> EediFrames:
    """Read the four frames written by `cache_processed`."""
    in_dir = Path(in_dir)
    return EediFrames(
        questions_df=pd.read_parquet(in_dir / "questions.parquet"),
        answer_options_df=pd.read_parquet(in_dir / "answer_options.parquet"),
        distractor_misconception_map_df=pd.read_parquet(
            in_dir / "distractor_misconception_map.parquet"
        ),
        misconception_catalogue_df=pd.read_parquet(in_dir / "misconception_catalogue.parquet"),
    )
