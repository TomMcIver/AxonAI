"""Tests for the ASSISTments loader.

Fixtures use rows shaped from the real 2009-2010 skill_builder schema
(user-provided sample columns + the standard `correct` column that the
loader requires). No fabricated dataset — fixtures exist only to exercise
loader code paths; real sample data will live at
data/raw/assistments_sample/ once committed.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from ml.simulator.data.assistments_loader import (
    DEFAULT_MIN_RESPONSES_PER_ITEM,
    build_skills_frame,
    cache_processed,
    load_processed,
    load_responses,
)


def _write_csv(path: Path, body: str) -> Path:
    path.write_text(dedent(body).lstrip())
    return path


@pytest.fixture
def minimal_csv(tmp_path: Path) -> Path:
    """Two items × a handful of responses each, enough to exercise schema."""
    return _write_csv(
        tmp_path / "assistments.csv",
        """
        user_id,problem_id,correct,skill_id,skill,start_time
        61394,61394,1,,,2012-09-28 15:11:27
        61394,365981,0,,Rounding,2012-10-09 11:01:52
        61394,426415,1,,Multiplication and Division Integers,2013-03-07 10:53:20
        61394,86686,1,,Proportion,2013-08-20 19:54:56
        76592,61394,0,,,2012-09-10 17:20:10
        76592,401234,1,,Exponents,2012-12-12 21:00:55
        """,
    )


@pytest.fixture
def filterable_csv(tmp_path: Path) -> Path:
    """One item with 150 responses and one with 2 — used for filter test."""
    rows = ["user_id,problem_id,correct"]
    for i in range(150):
        rows.append(f"{i},111,1")
    rows.append("1,222,0")
    rows.append("2,222,1")
    return _write_csv(tmp_path / "assistments.csv", "\n".join(rows) + "\n")


class TestLoadResponses:
    def test_schema_and_row_count(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        assert len(df) == 6
        assert set(df.columns) >= {"user_id", "problem_id", "correct", "skill_id", "skill_name"}

    def test_correct_coerced_to_bool(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        assert df["correct"].dtype == bool

    def test_blank_skills_get_sentinel(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        # First row has empty skill_name and blank skill_id in the CSV
        # (skill column was empty); the loader should assign sentinel -1.
        blank_rows = df[df["problem_id"] == 61394]
        assert (blank_rows["skill_id"] == -1).all()
        assert (blank_rows["skill_name"] == "").all()

    def test_skill_alias_mapped(self, minimal_csv: Path) -> None:
        # CSV uses 'skill' column; loader canonicalises to 'skill_name'.
        df = load_responses(minimal_csv, min_responses_per_item=1)
        assert "skill_name" in df.columns
        assert (df["skill_name"] == "Rounding").any()

    def test_timestamps_parsed(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        assert pd.api.types.is_datetime64_any_dtype(df["start_time"])

    def test_missing_required_column_raises(self, tmp_path: Path) -> None:
        bad = _write_csv(
            tmp_path / "no_correct.csv",
            """
            user_id,problem_id
            1,111
            """,
        )
        with pytest.raises(KeyError, match="correct"):
            load_responses(bad, min_responses_per_item=1)

    def test_min_responses_filter(self, filterable_csv: Path) -> None:
        # Default threshold is 150 — item 111 (150 responses) survives,
        # item 222 (2 responses) is dropped.
        df = load_responses(filterable_csv)  # default min_responses=150
        assert (df["problem_id"] == 111).all()
        assert len(df) == 150

    def test_filter_threshold_spec_default(self) -> None:
        assert DEFAULT_MIN_RESPONSES_PER_ITEM == 150


class TestBuildSkillsFrame:
    def test_unique_skills_emitted(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        skills = build_skills_frame(df)
        # Should dedupe: {-1 (blank), Rounding, Multiplication..., Proportion, Exponents}
        assert len(skills) == len(skills.drop_duplicates())
        assert "skill_id" in skills.columns

    def test_sorted_by_skill_id(self, minimal_csv: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        skills = build_skills_frame(df)
        ids = skills["skill_id"].dropna().tolist()
        assert ids == sorted(ids)


class TestCaching:
    def test_roundtrip_via_parquet(self, minimal_csv: Path, tmp_path: Path) -> None:
        df = load_responses(minimal_csv, min_responses_per_item=1)
        out = cache_processed(df, tmp_path / "processed" / "assistments.parquet")
        assert out.exists()
        reloaded = load_processed(out)
        pd.testing.assert_frame_equal(df, reloaded)
