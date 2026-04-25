"""Unit tests for ASSISTments ↔ Eedi semantic match (data prep + optional ST)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from ml.simulator.data.semantic_assistments_eedi_match import (
    _resolve_user_header,
    load_eedi_unique_question_texts,
    load_unique_assistment_item_texts,
)


def test_load_unique_assistment_item_texts_tiny(tmp_path: Path) -> None:
    p = tmp_path / "a.csv"
    p.write_text(
        "user_id,problem_id,correct,question_text\n"
        "1,10,1,What is 2+2?\n"
        "2,10,0,What is 2+2?\n"
        "3,20,1,Solve for x in x+1=3\n",
        encoding="utf-8",
    )
    df = load_unique_assistment_item_texts(p)
    assert len(df) == 2
    d = dict(zip(df["assistments_item_id"], df["assistments_text"], strict=True))
    assert d["10"] == "What is 2+2?"
    assert d["20"] == "Solve for x in x+1=3"


def test_resolve_user_header() -> None:
    assert _resolve_user_header("problem_id", ("problem_id", "question_text")) == "problem_id"
    with pytest.raises(KeyError):
        _resolve_user_header("nope", ("a", "b"))


def test_load_eedi_unique_tiny(tmp_path: Path) -> None:
    """Minimal Eedi 2024 train.csv shape required by the loader."""
    t = tmp_path / "train.csv"
    t.write_text(
        "QuestionId,ConstructId,ConstructName,SubjectId,SubjectName,CorrectAnswer,"
        "QuestionText,AnswerAText,AnswerBText,AnswerCText,AnswerDText\n"
        "1,0,S,0,M,A,Q one?,A0,B0,C0,D0\n"
        "2,0,S,0,M,B,Q two?,A1,B1,C1,D1\n"
        "2,0,S,0,M,B,Q two?,A1,B1,C1,D1\n",  # duplicate id
        encoding="utf-8",
    )
    q = load_eedi_unique_question_texts(t)
    assert len(q) == 2
    ids = set(q["eedi_question_id"].tolist())
    assert ids == {"1", "2"}


def test_run_end_to_end(tmp_path: Path) -> None:
    pytest.importorskip("sentence_transformers")
    pytest.importorskip("torch")
    from ml.simulator.data.semantic_assistments_eedi_match import run

    assist = tmp_path / "assistments.csv"
    assist.write_text(
        "user_id,problem_id,correct,question_text\n"
        "1,1,1,The sum of angles in a triangle is 180 degrees.\n",
        encoding="utf-8",
    )
    eed = tmp_path / "train.csv"
    eed.write_text(
        "QuestionId,ConstructId,ConstructName,SubjectId,SubjectName,CorrectAnswer,"
        "QuestionText,AnswerAText,AnswerBText,AnswerCText,AnswerDText\n"
        "99,0,S,0,M,A,Angles in a triangle add to one hundred eighty degrees.,a,b,c,d\n"
        "100,0,S,0,M,B,Completely different topic: photosynthesis in plants.,a,b,c,d\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    run(
        assistments_path=assist,
        eedi_questions_path=eed,
        out_csv=out,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        min_sim=0.5,  # loose for test stability
        top_k=2,
        encode_batch_size=8,
    )
    with out.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 1
    r0 = rows[0]
    assert "assistments_item_id" in r0 and "eedi_question_id" in r0
    assert "similarity_score" in r0
    # Best match for similar triangle text should be 99, not 100
    eedi_ids = {row["eedi_question_id"] for row in rows}
    assert "99" in eedi_ids
