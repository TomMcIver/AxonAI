"""Tests for LocalParquetWriter."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from ml.simulator.config import SimulationConfig
from ml.simulator.io.local_writer import LocalParquetWriter
from ml.simulator.loop.revise import ReviseRecord
from ml.simulator.loop.runner import SessionEndRecord
from ml.simulator.loop.teach import TeachRecord
from ml.simulator.student.profile import AttemptRecord


def _config() -> SimulationConfig:
    return SimulationConfig(
        n_students=1, term_weeks=1, sessions_per_week=1,
        minutes_per_session=20, subject="math", seed=7,
    )


class TestLocalParquetWriter:
    def test_writes_one_file_per_event_kind(self, tmp_path: Path) -> None:
        with LocalParquetWriter(tmp_path, "r1", _config()) as w:
            w.write(TeachRecord(student_id=1, concept_id=10, time=datetime(2024, 1, 1)))
            w.write(AttemptRecord(concept_id=10, item_id=100, is_correct=True,
                                  time=datetime(2024, 1, 1), response_time_ms=5000))
            w.write(ReviseRecord(student_id=1, concepts=(10, 11),
                                 time=datetime(2024, 1, 2)))
            w.write(SessionEndRecord(student_id=1, session_index=0,
                                     time=datetime(2024, 1, 2), attempts_in_session=1))

        run_dir = tmp_path / "r1"
        for kind in ("teach", "attempt", "revise", "session_end"):
            assert (run_dir / f"{kind}.parquet").exists()

    def test_every_row_tagged_is_simulated(self, tmp_path: Path) -> None:
        with LocalParquetWriter(tmp_path, "r1", _config()) as w:
            w.write(TeachRecord(student_id=1, concept_id=10, time=datetime(2024, 1, 1)))
            w.write(AttemptRecord(concept_id=10, item_id=100, is_correct=True,
                                  time=datetime(2024, 1, 1), response_time_ms=5000))

        run_dir = tmp_path / "r1"
        for kind in ("teach", "attempt"):
            table = pq.read_table(run_dir / f"{kind}.parquet")
            flags = table.column("is_simulated").to_pylist()
            assert all(flags)
            assert len(flags) == 1

    def test_manifest_records_counts_hash_and_seed(self, tmp_path: Path) -> None:
        cfg = _config()
        with LocalParquetWriter(tmp_path, "r1", cfg) as w:
            w.write(TeachRecord(student_id=1, concept_id=10, time=datetime(2024, 1, 1)))
            w.write(TeachRecord(student_id=1, concept_id=11, time=datetime(2024, 1, 1)))

        manifest = json.loads((tmp_path / "r1" / "manifest.json").read_text())
        assert manifest["seed"] == cfg.seed
        assert manifest["row_counts"]["teach"] == 2
        assert manifest["row_counts"]["attempt"] == 0
        assert manifest["is_simulated"] is True
        assert len(manifest["config_sha256"]) == 64  # sha256 hex

    def test_batches_flush_on_close(self, tmp_path: Path) -> None:
        # Fewer rows than batch size — exercises the close-time flush.
        with LocalParquetWriter(tmp_path, "r1", _config()) as w:
            for i in range(7):
                w.write(TeachRecord(student_id=1, concept_id=i, time=datetime(2024, 1, 1)))

        table = pq.read_table(tmp_path / "r1" / "teach.parquet")
        assert table.num_rows == 7

    def test_rejects_unknown_event_type(self, tmp_path: Path) -> None:
        with LocalParquetWriter(tmp_path, "r1", _config()) as w:
            with pytest.raises(TypeError):
                w.write(object())

    def test_revise_concepts_tuple_serialises_as_list(self, tmp_path: Path) -> None:
        with LocalParquetWriter(tmp_path, "r1", _config()) as w:
            w.write(ReviseRecord(student_id=1, concepts=(3, 5, 7),
                                 time=datetime(2024, 1, 2)))

        table = pq.read_table(tmp_path / "r1" / "revise.parquet")
        assert table.column("concepts").to_pylist() == [[3, 5, 7]]
