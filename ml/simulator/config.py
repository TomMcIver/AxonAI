"""`SimulationConfig` — the single source of every tunable constant.

Populated from YAML via `SimulationConfig.from_yaml(path)`. Magic numbers
elsewhere in the simulator are disallowed; every constant should trace
back to a field here or to an attributed paper citation.

Fields:
    n_students              — how many students to simulate.
    term_weeks              — term length in weeks.
    sessions_per_week       — sessions per student per week.
    minutes_per_session     — session duration (informational; the loop
                              spends response_time_ms per attempt).
    subject                 — e.g. "math"; informational.
    seed                    — master RNG seed (each student derives its
                              own seed deterministically from this).
    output_target           — "local_parquet" | "postgres".
    output_dir              — relative path under repo root (local_parquet).
    zpd_band                — (lower, upper) P(correct) for quiz selection.
    mastery_threshold       — BKT p_known above which the runner advances.
    session_interval_hours  — gap between sessions (drives forgetting).
    quiz_items_per_session  — attempts per newly-taught concept.
    revise_items_per_concept — attempts per revised concept.

See `docs/simulator_v1_plan.md §3` for the rationale behind each default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

OutputTarget = Literal["local_parquet", "postgres"]


@dataclass(frozen=True)
class SimulationConfig:
    n_students: int
    term_weeks: int
    sessions_per_week: int
    minutes_per_session: int
    subject: str
    seed: int
    output_target: OutputTarget = "local_parquet"
    output_dir: str = "data/processed/runs"
    zpd_band: tuple[float, float] = (0.60, 0.85)
    mastery_threshold: float = 0.85
    session_interval_hours: float = 24.0
    quiz_items_per_session: int = 5
    revise_items_per_concept: int = 1

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SimulationConfig":
        with open(path, "r") as f:
            raw: dict[str, Any] = yaml.safe_load(f)
        # Tuples arrive from YAML as lists; normalise.
        if "zpd_band" in raw and isinstance(raw["zpd_band"], list):
            raw["zpd_band"] = tuple(raw["zpd_band"])
        return cls(**raw)

    @property
    def n_sessions(self) -> int:
        return self.term_weeks * self.sessions_per_week
