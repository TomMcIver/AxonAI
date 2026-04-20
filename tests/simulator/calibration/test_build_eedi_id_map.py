"""Tests for `ml.simulator.calibration.build_eedi_id_map` (PR B1)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.simulator.calibration import build_eedi_id_map


def _write_questions_csv(path: Path, misc_ids: list[int | None]) -> None:
    """Emit a minimal Eedi-shaped questions CSV.

    We need enough columns for the loader's _require_columns check and a
    MisconceptionBId column populated from `misc_ids`.
    """
    rows = []
    for i, mid in enumerate(misc_ids):
        rows.append(
            {
                "QuestionId": i,
                "ConstructId": 1000 + i,
                "ConstructName": "c",
                "SubjectId": 1,
                "SubjectName": "s",
                "CorrectAnswer": "A",
                "QuestionText": "q",
                "AnswerAText": "a",
                "AnswerBText": "b",
                "AnswerCText": "c",
                "AnswerDText": "d",
                "MisconceptionAId": None,
                "MisconceptionBId": mid,
                "MisconceptionCId": None,
                "MisconceptionDId": None,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_mapping_csv(path: Path, entries: list[tuple[int, str]]) -> None:
    pd.DataFrame(entries, columns=["MisconceptionId", "MisconceptionName"]).to_csv(
        path, index=False
    )


def test_build_passthrough_ids_sorted(tmp_path: Path):
    q = tmp_path / "questions.csv"
    m = tmp_path / "mapping.csv"
    _write_questions_csv(q, [7, 0, 11, 2, 7])
    _write_mapping_csv(
        m,
        [
            (7, "Name seven"),
            (0, "Name zero"),
            (11, "Name eleven"),
            (2, "Name two"),
        ],
    )
    out = tmp_path / "id_map.json"
    build_eedi_id_map.build(str(q), str(m), str(out))
    payload = json.loads(out.read_text())
    ids = [e["eedi_id"] for e in payload["entries"]]
    assert ids == sorted(ids)
    # Preserves the Eedi integer IDs as-is.
    assert set(ids) == {0, 2, 7, 11}


def test_build_indexes_are_dense(tmp_path: Path):
    q = tmp_path / "questions.csv"
    m = tmp_path / "mapping.csv"
    _write_questions_csv(q, [5, 10, 15])
    _write_mapping_csv(m, [(5, "a"), (10, "b"), (15, "c")])
    out = tmp_path / "id_map.json"
    build_eedi_id_map.build(str(q), str(m), str(out))
    payload = json.loads(out.read_text())
    for i, e in enumerate(payload["entries"]):
        assert e["index"] == i


def test_meta_block(tmp_path: Path):
    q = tmp_path / "questions.csv"
    m = tmp_path / "mapping.csv"
    _write_questions_csv(q, [5, 10, 15])
    _write_mapping_csv(m, [(5, "a"), (10, "b"), (15, "c")])
    out = tmp_path / "id_map.json"
    build_eedi_id_map.build(str(q), str(m), str(out))
    payload = json.loads(out.read_text())
    assert payload["_meta"]["n_misconceptions"] == 3
    assert payload["_meta"]["id_min"] == 5
    assert payload["_meta"]["id_max"] == 15
    assert payload["_meta"]["source_csv"] == str(q)
    assert payload["_meta"]["mapping_csv"] == str(m)


def test_build_idempotent(tmp_path: Path):
    q = tmp_path / "questions.csv"
    m = tmp_path / "mapping.csv"
    _write_questions_csv(q, [5, 10, 15])
    _write_mapping_csv(m, [(5, "a"), (10, "b"), (15, "c")])
    out = tmp_path / "id_map.json"
    build_eedi_id_map.build(str(q), str(m), str(out))
    first = out.read_text()
    build_eedi_id_map.build(str(q), str(m), str(out))
    second = out.read_text()
    assert first == second


def test_load_id_map_roundtrip(tmp_path: Path):
    q = tmp_path / "questions.csv"
    m = tmp_path / "mapping.csv"
    _write_questions_csv(q, [5, 10, 15])
    _write_mapping_csv(m, [(5, "a"), (10, "b"), (15, "c")])
    out = tmp_path / "id_map.json"
    build_eedi_id_map.build(str(q), str(m), str(out))
    ids = build_eedi_id_map.load_id_map(out)
    assert ids == [5, 10, 15]
