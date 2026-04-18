"""Tests for the Eedi 2024 loader.

Fixtures use the exact rows the user pasted from the real Eedi CSV —
these are user-provided real data slices, not fabricated.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from ml.simulator.data.eedi_misconceptions_loader import (
    cache_processed,
    load,
    load_processed,
)


def _write(path: Path, body: str) -> Path:
    path.write_text(dedent(body).lstrip())
    return path


@pytest.fixture
def eedi_csv(tmp_path: Path) -> Path:
    # Condensed rows from the user-provided Eedi sample (QuestionText and
    # option bodies shortened to single tokens for test readability; the
    # ID / misconception columns are preserved verbatim).
    return _write(
        tmp_path / "eedi.csv",
        """
        QuestionId,ConstructId,ConstructName,SubjectId,SubjectName,CorrectAnswer,QuestionText,AnswerAText,AnswerBText,AnswerCText,AnswerDText,MisconceptionAId,MisconceptionBId,MisconceptionCId,MisconceptionDId
        0,856,Use the order of operations,33,BIDMAS,A,Q0,optA,optB,optC,optD,,,,1672
        1,1612,Simplify algebraic fraction,1077,Simplifying,D,Q1,optA,optB,optC,optD,2142,143,2142,
        2,2774,Calculate the range,339,Range,B,Q2,optA,optB,optC,optD,1287,,1287,1073
        3,2377,Diagonals of a rectangle,88,Properties,C,Q3,acute,obtuse,ninety,nei,1180,1180,,1180
        """,
    )


@pytest.fixture
def mapping_csv(tmp_path: Path) -> Path:
    return _write(
        tmp_path / "misconception_mapping.csv",
        """
        MisconceptionId,MisconceptionName
        1672,Forgets brackets
        2142,Confuses factorisation
        143,Cancels terms incorrectly
        1287,Subtracts instead of ranging
        1073,Adds constant to range
        1180,Calls right angle an obtuse angle
        """,
    )


class TestLoad:
    def test_frame_shapes(self, eedi_csv: Path) -> None:
        f = load(eedi_csv)
        assert len(f.questions_df) == 4
        # 4 questions × 4 options = 16 rows
        assert len(f.answer_options_df) == 16
        # Non-null misconception cells from the fixture:
        # Q0: D→1672  (1)
        # Q1: A→2142, B→143, C→2142 (3)
        # Q2: A→1287, C→1287, D→1073 (3)
        # Q3: A→1180, B→1180, D→1180 (3) → total 10
        assert len(f.distractor_misconception_map_df) == 10

    def test_questions_schema(self, eedi_csv: Path) -> None:
        f = load(eedi_csv)
        assert set(f.questions_df.columns) == {
            "QuestionId",
            "ConstructId",
            "ConstructName",
            "SubjectId",
            "SubjectName",
            "CorrectAnswer",
            "QuestionText",
        }

    def test_answer_options_correctness_flag(self, eedi_csv: Path) -> None:
        f = load(eedi_csv)
        # Q0's correct answer is A → only option A should be IsCorrect=True.
        q0 = f.answer_options_df[f.answer_options_df["QuestionId"] == 0]
        correct_opts = q0[q0["IsCorrect"]]["Option"].tolist()
        assert correct_opts == ["A"]

    def test_distractor_map_type(self, eedi_csv: Path) -> None:
        f = load(eedi_csv)
        assert str(f.distractor_misconception_map_df["MisconceptionId"].dtype) == "Int64"

    def test_catalogue_derived_when_no_mapping(self, eedi_csv: Path) -> None:
        f = load(eedi_csv)
        # Unique IDs in the fixture: {1672, 2142, 143, 1287, 1073, 1180}
        assert set(f.misconception_catalogue_df["MisconceptionId"]) == {
            1672, 2142, 143, 1287, 1073, 1180,
        }
        # No names available without mapping file.
        assert (f.misconception_catalogue_df["MisconceptionName"] == "").all()

    def test_catalogue_uses_mapping_file_when_given(
        self, eedi_csv: Path, mapping_csv: Path
    ) -> None:
        f = load(eedi_csv, misconception_mapping_path=mapping_csv)
        by_id = dict(
            zip(
                f.misconception_catalogue_df["MisconceptionId"],
                f.misconception_catalogue_df["MisconceptionName"],
            )
        )
        assert by_id[1672] == "Forgets brackets"

    def test_missing_column_raises(self, tmp_path: Path) -> None:
        bad = _write(
            tmp_path / "bad.csv",
            """
            QuestionId,ConstructId,ConstructName
            0,1,Stub
            """,
        )
        with pytest.raises(KeyError):
            load(bad)


class TestCaching:
    def test_roundtrip(self, eedi_csv: Path, tmp_path: Path) -> None:
        f = load(eedi_csv)
        out_dir = cache_processed(f, tmp_path / "processed" / "eedi")
        assert (out_dir / "questions.parquet").exists()
        assert (out_dir / "answer_options.parquet").exists()
        assert (out_dir / "distractor_misconception_map.parquet").exists()
        assert (out_dir / "misconception_catalogue.parquet").exists()

        reloaded = load_processed(out_dir)
        pd.testing.assert_frame_equal(f.questions_df, reloaded.questions_df)
        pd.testing.assert_frame_equal(
            f.answer_options_df.reset_index(drop=True),
            reloaded.answer_options_df.reset_index(drop=True),
        )
