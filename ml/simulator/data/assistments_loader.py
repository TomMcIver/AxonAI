"""ASSISTments Skill Builder (Heffernan & Heffernan, 2014) loader.

This is the IRT/BKT calibration dataset for v1. The classic 2009-2010
release includes per-student per-problem responses with correctness,
skill tags, timestamps, and hint counts.

Expected columns (case-insensitive, superset tolerated):

    Required   user_id (int)
               problem_id (int)
               correct (0/1 or bool-like)
    Strongly recommended
               skill_id (int)    or  skill_name (str)
               start_time (datetime parseable)
    Optional   end_time, ms_first_response, hint_count, attempt_count,
               original, assignment_id, assistment_id, problem_type

Missing-skill handling: the released CSVs frequently carry blank skill
tags for un-tagged items (e.g. problem_type == 'choose_1'). Rows with
a blank / NA skill are retained but the skill_id is set to -1 and
skill_name to '' — the calibrator in PR 5 decides whether to include
them.

Filter: items with fewer than `min_responses` responses (default 150,
per the spec; IRT stability guidance from G. Brown) are dropped.

Cache: write the processed DataFrame as parquet under data/processed/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from ml.simulator.data.s3_io import is_s3_uri, materialise

# Spec default — 2PL IRT stability lower bound per G. Brown.
DEFAULT_MIN_RESPONSES_PER_ITEM = 150

# Columns the loader is willing to pass through, in the order it prefers
# them if several aliases exist. Unused columns are dropped to keep the
# processed DataFrame small.
_PASSTHROUGH_COLUMNS = [
    "user_id",
    "problem_id",
    "problem_log_id",
    "correct",
    "skill_id",
    "skill_name",
    "start_time",
    "end_time",
    "ms_first_response",
    "hint_count",
    "attempt_count",
    "original",
    "assignment_id",
    "assistment_id",
    "problem_type",
]

# Alias map: CSV column → canonical name. Applied case-insensitively.
_ALIASES = {
    "skill": "skill_name",
    "problem_log_id": "problem_log_id",
}


def _canonicalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase columns and apply known aliases."""
    renamed = {}
    for col in df.columns:
        low = col.strip().lower()
        low = _ALIASES.get(low, low)
        renamed[col] = low
    return df.rename(columns=renamed)


def _require_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            f"ASSISTments CSV missing required columns: {missing}. "
            f"Present columns: {sorted(df.columns.tolist())}"
        )


def load_responses(
    path: Path | str,
    min_responses_per_item: int = DEFAULT_MIN_RESPONSES_PER_ITEM,
) -> pd.DataFrame:
    """Load an ASSISTments responses CSV and return a tidy DataFrame.

    Returns one row per response with the canonical columns listed in
    `_PASSTHROUGH_COLUMNS` (whichever of them are present, plus derived
    `skill_id` / `skill_name` for rows with a blank skill).

    Items with fewer than `min_responses_per_item` responses are dropped
    (spec: IRT stability).

    Accepts either a local path or an `s3://bucket/key` URI. S3 objects
    are downloaded into the local cache before parsing.
    """
    local = materialise(path) if is_s3_uri(str(path)) else Path(path)
    df = pd.read_csv(local, low_memory=False)
    df = _canonicalise_columns(df)

    _require_columns(df, ("user_id", "problem_id", "correct"))

    # Normalise correctness into a boolean. Source values may be int or
    # strings like "1.0" / "0".
    df["correct"] = df["correct"].astype(float).astype(bool)

    # Backfill skill_id / skill_name for rows that only have one of them.
    if "skill_id" not in df.columns:
        df["skill_id"] = pd.NA
    if "skill_name" not in df.columns:
        df["skill_name"] = ""
    # read_csv maps blank cells to NaN; normalise skill_name into a string
    # so the blank-skill mask can compare against "" cleanly.
    df["skill_name"] = df["skill_name"].fillna("").astype(str).str.strip()
    blank_skill_mask = df["skill_id"].isna() & (df["skill_name"] == "")
    df.loc[blank_skill_mask, "skill_id"] = -1
    df.loc[blank_skill_mask, "skill_name"] = ""

    # Parse timestamps if present.
    for ts in ("start_time", "end_time"):
        if ts in df.columns:
            df[ts] = pd.to_datetime(df[ts], errors="coerce")

    # Keep only the passthrough columns that actually exist.
    keep = [c for c in _PASSTHROUGH_COLUMNS if c in df.columns]
    df = df[keep].copy()

    # Filter items below the IRT stability threshold.
    counts = df.groupby("problem_id").size()
    kept_items = counts[counts >= min_responses_per_item].index
    df = df[df["problem_id"].isin(kept_items)].reset_index(drop=True)

    return df


def build_skills_frame(responses_df: pd.DataFrame) -> pd.DataFrame:
    """Derive a unique (skill_id, skill_name) table from the responses."""
    if "skill_id" not in responses_df.columns:
        raise KeyError("responses_df must contain skill_id after load_responses()")
    skill_name_col = "skill_name" if "skill_name" in responses_df.columns else None
    cols = ["skill_id"] + ([skill_name_col] if skill_name_col else [])
    skills = (
        responses_df[cols]
        .drop_duplicates()
        .sort_values("skill_id")
        .reset_index(drop=True)
    )
    return skills


def cache_processed(
    responses_df: pd.DataFrame,
    out_path: Path | str,
) -> Path:
    """Write the processed responses DataFrame to parquet."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    responses_df.to_parquet(out_path, index=False)
    return out_path


def load_processed(path: Path | str) -> pd.DataFrame:
    """Read a cached parquet produced by `cache_processed`."""
    return pd.read_parquet(path)
