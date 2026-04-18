"""Tests for SimulationConfig."""

from __future__ import annotations

from pathlib import Path

import pytest

from ml.simulator.config import SimulationConfig


class TestSimulationConfig:
    def test_loads_small_yaml(self) -> None:
        path = Path("ml/simulator/configs/small.yaml")
        cfg = SimulationConfig.from_yaml(path)
        assert cfg.n_students == 10
        assert cfg.term_weeks == 1
        assert cfg.output_target == "local_parquet"
        assert cfg.zpd_band == (0.60, 0.85)

    def test_loads_full_yaml(self) -> None:
        path = Path("ml/simulator/configs/full.yaml")
        cfg = SimulationConfig.from_yaml(path)
        assert cfg.n_students == 3000
        assert cfg.term_weeks == 10

    def test_n_sessions_derived(self) -> None:
        cfg = SimulationConfig(
            n_students=1, term_weeks=10, sessions_per_week=3,
            minutes_per_session=20, subject="math", seed=0,
        )
        assert cfg.n_sessions == 30

    def test_frozen(self) -> None:
        cfg = SimulationConfig(
            n_students=1, term_weeks=1, sessions_per_week=1,
            minutes_per_session=20, subject="math", seed=0,
        )
        with pytest.raises(Exception):
            cfg.n_students = 9999  # type: ignore[misc]
