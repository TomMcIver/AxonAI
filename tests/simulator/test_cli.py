"""Tests for the CLI smoke path."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from ml.simulator.cli import main


class TestCliRun:
    def test_smoke_run_writes_parquet_and_manifest(self, tmp_path: Path) -> None:
        config_path = Path("ml/simulator/configs/small.yaml")
        rc = main([
            "run",
            "--config", str(config_path),
            "--run-id", "smoke1",
            "--output-dir", str(tmp_path),
        ])
        assert rc == 0
        run_dir = tmp_path / "smoke1"
        manifest = json.loads((run_dir / "manifest.json").read_text())
        assert manifest["row_counts"]["session_end"] > 0
        assert manifest["row_counts"]["attempt"] > 0
        attempts = pq.read_table(run_dir / "attempt.parquet")
        assert attempts.num_rows == manifest["row_counts"]["attempt"]
        assert all(attempts.column("is_simulated").to_pylist())

    def test_deterministic_given_seed(self, tmp_path: Path) -> None:
        config_path = Path("ml/simulator/configs/small.yaml")
        main(["run", "--config", str(config_path),
              "--run-id", "a", "--output-dir", str(tmp_path)])
        main(["run", "--config", str(config_path),
              "--run-id", "b", "--output-dir", str(tmp_path)])
        t_a = pq.read_table(tmp_path / "a" / "attempt.parquet").to_pylist()
        t_b = pq.read_table(tmp_path / "b" / "attempt.parquet").to_pylist()
        assert t_a == t_b


class TestCliValidate:
    def test_validate_not_implemented_yet(self) -> None:
        rc = main(["validate", "--run-id", "x"])
        assert rc == 1
