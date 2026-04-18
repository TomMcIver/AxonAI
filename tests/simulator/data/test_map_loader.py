"""Tests for the MAP loader.

Fixture rows come directly from the user-provided sample — real data,
just four rows for the first question (31772).
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from ml.simulator.data.map_loader import cache_processed, load_explanations, load_processed


def _write(path: Path, body: str) -> Path:
    path.write_text(dedent(body).lstrip())
    return path


@pytest.fixture
def map_csv(tmp_path: Path) -> Path:
    # Real rows from the user's MAP paste (explanations preserved verbatim).
    return _write(
        tmp_path / "map.csv",
        """
        row_id,QuestionId,QuestionText,MC_Answer,StudentExplanation,Category,Misconception
        0,31772,"What fraction of the shape is not shaded?","\\( \\frac{1}{3} \\)","0ne third is equal to tree nineth",True_Correct,NA
        1,31772,"What fraction of the shape is not shaded?","\\( \\frac{1}{3} \\)","1 / 3 because 6 over 9 is 2 thirds",True_Correct,NA
        2,31772,"What fraction of the shape is not shaded?","\\( \\frac{1}{3} \\)","1 3rd is half of 3 6th",True_Neither,NA
        3,31772,"What fraction of the shape is not shaded?","\\( \\frac{1}{3} \\)","1 goes into everything and 3 goes into nine",True_Neither,NA
        """,
    )


class TestLoadExplanations:
    def test_schema_and_row_count(self, map_csv: Path) -> None:
        df = load_explanations(map_csv)
        assert len(df) == 4
        assert list(df.columns) == [
            "row_id",
            "QuestionId",
            "QuestionText",
            "MC_Answer",
            "StudentExplanation",
            "Category",
            "Misconception",
        ]

    def test_na_sentinel_converted(self, map_csv: Path) -> None:
        df = load_explanations(map_csv)
        # All four fixture rows have 'NA' — should become pandas NA.
        assert df["Misconception"].isna().all()

    def test_categories_preserved(self, map_csv: Path) -> None:
        df = load_explanations(map_csv)
        assert set(df["Category"]) == {"True_Correct", "True_Neither"}

    def test_missing_column_raises(self, tmp_path: Path) -> None:
        bad = _write(
            tmp_path / "bad.csv",
            """
            row_id,QuestionId,QuestionText
            0,1,Q
            """,
        )
        with pytest.raises(KeyError):
            load_explanations(bad)


class TestCaching:
    def test_roundtrip(self, map_csv: Path, tmp_path: Path) -> None:
        df = load_explanations(map_csv)
        out = cache_processed(df, tmp_path / "processed" / "map.parquet")
        assert out.exists()
        reloaded = load_processed(out)
        pd.testing.assert_frame_equal(df, reloaded)
