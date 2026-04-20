"""Unit tests for the concept-graph validation runner.

Exercises the pure-function helpers (split, scoring, precision) against
hand-constructed graphs so the logic is verified without needing the
ASSISTments CSV.
"""

from __future__ import annotations

import json

import networkx as nx
import pandas as pd
import pytest

from ml.simulator.calibration.run_concept_graph_validation import (
    _load_gold,
    _metrics,
    _precision_on_gold_subgraph,
    _score_gold_edges,
    _split_users,
)


def _gold(edges: list[tuple[int, int]]) -> list[dict]:
    return [
        {
            "prereq_id": a,
            "successor_id": b,
            "prereq_name": f"s{a}",
            "successor_name": f"s{b}",
        }
        for a, b in edges
    ]


def test_split_users_partitions_by_user_id():
    df = pd.DataFrame(
        {"user_id": list(range(100)) * 2, "problem_id": [0] * 200, "correct": [True] * 200}
    )
    train, held = _split_users(df, train_fraction=0.8, seed=1)
    train_users = set(train["user_id"])
    held_users = set(held["user_id"])
    assert len(train_users & held_users) == 0
    assert len(train_users) == 80
    assert len(held_users) == 20


def test_split_users_is_deterministic_under_seed():
    df = pd.DataFrame({"user_id": list(range(50)), "problem_id": [0] * 50, "correct": [True] * 50})
    a_train, a_held = _split_users(df, 0.7, seed=42)
    b_train, b_held = _split_users(df, 0.7, seed=42)
    assert set(a_train["user_id"]) == set(b_train["user_id"])
    assert set(a_held["user_id"]) == set(b_held["user_id"])


def test_score_gold_direct_hit():
    g = nx.DiGraph()
    g.add_edge(1, 2)
    diag = _score_gold_edges(_gold([(1, 2)]), g)
    assert diag[0].direct_edge is True
    assert diag[0].transitive_path is True
    assert diag[0].path_length == 1
    assert diag[0].status() == "direct_hit"


def test_score_gold_transitive_path():
    g = nx.DiGraph()
    g.add_edges_from([(1, 3), (3, 2)])  # 1 -> 3 -> 2
    diag = _score_gold_edges(_gold([(1, 2)]), g)
    assert diag[0].direct_edge is False
    assert diag[0].transitive_path is True
    assert diag[0].path_length == 2
    assert diag[0].status() == "transitive_hit"


def test_score_gold_missing_when_no_path():
    g = nx.DiGraph()
    g.add_nodes_from([1, 2])
    diag = _score_gold_edges(_gold([(1, 2)]), g)
    assert diag[0].status() == "missing"
    assert diag[0].path_length == 0


def test_score_gold_node_dropped():
    g = nx.DiGraph()
    g.add_node(1)  # successor 2 absent
    diag = _score_gold_edges(_gold([(1, 2)]), g)
    assert diag[0].status() == "gold_node_dropped"


def test_metrics_counts_and_recall():
    g = nx.DiGraph()
    g.add_edge(1, 2)
    g.add_edges_from([(3, 5), (5, 4)])  # 3 -> 4 transitive
    g.add_nodes_from([6, 7])
    # Gold: direct hit, transitive, missing, node-dropped.
    gold = _gold([(1, 2), (3, 4), (6, 7), (8, 9)])
    diag = _score_gold_edges(gold, g)
    m = _metrics(diag)
    assert m["n_direct_hits"] == 1
    assert m["n_transitive_hits"] == 1
    assert m["n_missing"] == 1
    assert m["n_gold_nodes_dropped"] == 1
    assert m["n_evaluable_gold_edges"] == 3
    assert m["direct_recall"] == pytest.approx(1 / 3)
    assert m["path_recall"] == pytest.approx(2 / 3)


def test_precision_counts_tp_and_fp_against_gold_closure():
    # Gold: 1 -> 2 and 2 -> 3 (so 1 ~> 3 is in gold transitive closure).
    gold = _gold([(1, 2), (2, 3)])
    g = nx.DiGraph()
    g.add_edges_from([(1, 2), (2, 3), (3, 1)])  # 3 -> 1 is a false edge
    # Inferred descendants: 1->{2,3}, 2->{3,1}, 3->{1,2}. Gold nodes {1,2,3}.
    # Over gold nodes, pair-paths: (1,2),(1,3),(2,3),(2,1),(3,1),(3,2).
    # Gold transitive closure: (1,2),(1,3),(2,3). TP=3, FP=3.
    p = _precision_on_gold_subgraph(gold, g)
    assert p["n_tp"] == 3
    assert p["n_fp"] == 3
    assert p["precision"] == pytest.approx(0.5)
    assert p["n_gold_nodes_in_graph"] == 3
    assert p["n_gold_nodes_total"] == 3


def test_load_gold_reads_edges(tmp_path):
    p = tmp_path / "gold.json"
    p.write_text(
        json.dumps(
            {
                "_meta": {"n_edges": 1},
                "edges": [
                    {
                        "prereq_id": 10,
                        "successor_id": 20,
                        "prereq_name": "a",
                        "successor_name": "b",
                    }
                ],
            }
        )
    )
    edges = _load_gold(p)
    assert len(edges) == 1
    assert edges[0]["prereq_id"] == 10
