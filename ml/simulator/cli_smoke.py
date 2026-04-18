"""Smoke-run glue: config → generator → runner → writer.

PR 9's CLI `run` subcommand targets this path. It uses a small synthetic
item bank + concept graph (3 concepts, 3 items each) so the wiring can
be exercised without the full calibration artefacts, which only land
end-to-end in PR 10.

PR 10 will replace `_build_demo_world` with a loader that reads the
fitted item bank + concept graph + bkt params from disk.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np

from ml.simulator.config import SimulationConfig
from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.io.local_writer import LocalParquetWriter
from ml.simulator.loop.runner import TermRunner
from ml.simulator.psychometrics.bkt import BKTParams, BKTState
from ml.simulator.student.profile import StudentProfile


def _build_demo_world() -> tuple[ConceptGraph, ItemBank, dict[int, BKTParams]]:
    g = nx.DiGraph()
    g.add_edges_from([(1, 2), (2, 3)])
    graph = ConceptGraph(g)

    items: list[Item] = []
    for concept in (1, 2, 3):
        for k in range(3):
            items.append(
                Item(
                    item_id=concept * 100 + k,
                    concept_id=concept,
                    a=1.2,
                    b=-0.5 + 0.5 * k,
                )
            )
    bank = ItemBank(items)

    bkt = {
        c: BKTParams(p_init=0.2, p_transit=0.2, p_slip=0.08, p_guess=0.2)
        for c in (1, 2, 3)
    }
    return graph, bank, bkt


def _student(student_id: int, rng: np.random.Generator) -> StudentProfile:
    base = float(rng.normal(0.0, 1.0))
    return StudentProfile(
        student_id=student_id,
        true_theta={c: base + float(rng.normal(0.0, 0.3)) for c in (1, 2, 3)},
        estimated_theta={c: (0.0, 1.0) for c in (1, 2, 3)},
        bkt_state={c: BKTState(p_known=0.2) for c in (1, 2, 3)},
        elo_rating=1200.0,
        recall_half_life={c: 24.0 for c in (1, 2, 3)},
        last_retrieval={},
        learning_rate=0.15,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(math.log(8000.0), 0.3),
        attempts_history=[],
    )


def smoke_run(config: SimulationConfig, run_id: str, output_dir: str | Path) -> None:
    graph, bank, bkt = _build_demo_world()
    master_rng = np.random.default_rng(config.seed)
    start_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)

    with LocalParquetWriter(output_dir, run_id, config) as writer:
        for i in range(config.n_students):
            student_seed = int(master_rng.integers(0, 2**31 - 1))
            student_rng = np.random.default_rng(student_seed)
            profile = _student(student_id=i, rng=student_rng)
            runner = TermRunner(
                student=profile,
                concept_graph=graph,
                item_bank=bank,
                bkt_params_by_concept=bkt,
                start_time=start_time,
                n_sessions=config.n_sessions,
                session_interval_hours=config.session_interval_hours,
                quiz_items_per_session=config.quiz_items_per_session,
                revise_items_per_concept=config.revise_items_per_concept,
                seed=student_seed,
            )
            for event in runner.run():
                writer.write(event)
