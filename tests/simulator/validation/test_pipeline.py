"""End-to-end self-consistency tests on the validation pipeline.

Scaled down so they run in a few seconds; the real report generation
is manual via `python -m ml.simulator.validation.run_validation`.
"""

from __future__ import annotations

import json
from pathlib import Path

from ml.simulator.validation.pipeline import run_validation
from ml.simulator.validation.run_validation import main as validation_main


class TestRunValidation:
    def test_runs_end_to_end_and_recovers_difficulty(self) -> None:
        report = run_validation(
            n_truth_students=200,
            n_skills=3,
            items_per_skill=8,
            n_sim_students=50,
            n_sessions=6,
            seed=42,
        )
        assert report.fit_2pl_converged
        # b recovery is the most reliable signal at this scale.
        assert report.recovery_2pl["b_pearson"] > 0.8
        # Theta recovers strongly with enough students.
        assert report.recovery_theta["theta_pearson"] > 0.7
        # Config.n_sessions must match what the loop actually ran.
        assert report.n_sessions == 6

    def test_deterministic_given_seed(self) -> None:
        a = run_validation(
            n_truth_students=80, n_skills=2, items_per_skill=5,
            n_sim_students=20, n_sessions=4, seed=7,
        )
        b = run_validation(
            n_truth_students=80, n_skills=2, items_per_skill=5,
            n_sim_students=20, n_sessions=4, seed=7,
        )
        assert a.to_dict() == b.to_dict()

    def test_writes_parquet_when_output_dir_given(self, tmp_path: Path) -> None:
        run_validation(
            n_truth_students=60, n_skills=2, items_per_skill=4,
            n_sim_students=10, n_sessions=3, seed=0,
            parquet_output_dir=tmp_path, run_id="val",
        )
        run_dir = tmp_path / "val"
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "attempt.parquet").exists()


class TestValidationCli:
    def test_writes_json_report(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        rc = validation_main([
            "--out-json", str(out),
            "--seed", "0",
            "--n-truth-students", "60",
            "--n-skills", "2",
            "--items-per-skill", "4",
            "--n-sim-students", "10",
            "--n-sessions", "3",
        ])
        assert rc == 0
        report = json.loads(out.read_text())
        assert report["n_truth_students"] == 60
        assert report["fit_2pl_converged"] is True
