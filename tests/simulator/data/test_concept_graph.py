"""Tests for the co-occurrence concept graph builder.

Synthetic responses with a known ordering are constructed, then we
check the derived DAG matches expectations.
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

from ml.simulator.data.concept_graph import (
    ConceptGraph,
    _acyclic_from_ranked_edges,
    _candidate_edges,
    _first_touch_per_skill,
    _pairwise_ordering_counts,
    build_concept_graph,
)


def _chain_responses(
    n_students: int,
    chain: list[int],
    start_day: str = "2024-01-01",
) -> pd.DataFrame:
    """Every student sees skills in the given order, one day apart."""
    rows = []
    for user in range(n_students):
        base = pd.Timestamp(start_day)
        for day, skill in enumerate(chain):
            rows.append(
                {
                    "user_id": user,
                    "problem_id": skill * 1000 + day,
                    "skill_id": skill,
                    "correct": True,
                    "start_time": base + pd.Timedelta(days=day),
                }
            )
    return pd.DataFrame(rows)


class TestFirstTouch:
    def test_one_row_per_user_skill(self) -> None:
        df = _chain_responses(n_students=3, chain=[1, 2, 3])
        ft = _first_touch_per_skill(df)
        assert len(ft) == 9
        assert set(ft.columns) == {"user_id", "skill_id", "first_time"}

    def test_excludes_untagged(self) -> None:
        df = _chain_responses(n_students=2, chain=[1, 2])
        df.loc[df["skill_id"] == 2, "skill_id"] = -1
        ft = _first_touch_per_skill(df)
        assert (ft["skill_id"] == -1).sum() == 0

    def test_requires_start_time(self) -> None:
        df = _chain_responses(n_students=1, chain=[1]).drop(columns="start_time")
        with pytest.raises(KeyError):
            _first_touch_per_skill(df)


class TestPairwiseCounts:
    def test_chain_produces_expected_before_counts(self) -> None:
        df = _chain_responses(n_students=5, chain=[1, 2, 3])
        ft = _first_touch_per_skill(df)
        before, overlap = _pairwise_ordering_counts(ft)
        # 5 students each saw 1 before 2, 1 before 3, 2 before 3.
        assert before[(1, 2)] == 5
        assert before[(1, 3)] == 5
        assert before[(2, 3)] == 5
        # No one saw them the other way.
        assert before.get((2, 1), 0) == 0
        assert overlap[(1, 2)] == 5

    def test_split_population(self) -> None:
        # Half-half: 3 students see 1→2, 2 students see 2→1.
        df_a = _chain_responses(n_students=3, chain=[1, 2])
        df_b = _chain_responses(n_students=2, chain=[2, 1])
        df_b["user_id"] += 100  # distinct users
        df = pd.concat([df_a, df_b]).reset_index(drop=True)
        ft = _first_touch_per_skill(df)
        before, overlap = _pairwise_ordering_counts(ft)
        assert before[(1, 2)] == 3
        assert before[(2, 1)] == 2
        assert overlap[(1, 2)] == 5


class TestCandidateEdges:
    def test_emits_edge_when_above_threshold(self) -> None:
        before = {(1, 2): 25, (2, 1): 5}
        overlap = {(1, 2): 30}
        edges = _candidate_edges(before, overlap, min_overlap=20, order_threshold=0.7)
        assert len(edges) == 1
        a, b, ratio, support = edges[0]
        assert (a, b) == (1, 2)
        assert ratio == pytest.approx(25 / 30)
        assert support == 30

    def test_drops_low_overlap(self) -> None:
        before = {(1, 2): 5}
        overlap = {(1, 2): 5}
        edges = _candidate_edges(before, overlap, min_overlap=20, order_threshold=0.5)
        assert edges == []

    def test_drops_ambiguous_ordering(self) -> None:
        # 15/30 is below the 0.7 threshold in both directions.
        before = {(1, 2): 15, (2, 1): 15}
        overlap = {(1, 2): 30}
        edges = _candidate_edges(before, overlap, min_overlap=20, order_threshold=0.7)
        assert edges == []


class TestAcyclicConstruction:
    def test_breaks_cycles_weakest_last(self) -> None:
        # Three skills: 1→2 (strong), 2→3 (strong), 3→1 (weak).
        edges = [
            (1, 2, 0.95, 100),
            (2, 3, 0.92, 100),
            (3, 1, 0.75, 30),
        ]
        g = _acyclic_from_ranked_edges([1, 2, 3], edges)
        assert nx.is_directed_acyclic_graph(g)
        # The weaker back-edge should be dropped.
        assert not g.has_edge(3, 1)
        assert g.has_edge(1, 2)
        assert g.has_edge(2, 3)


class TestConceptGraph:
    def test_rejects_cyclic_input(self) -> None:
        g = nx.DiGraph()
        g.add_edges_from([(1, 2), (2, 1)])
        with pytest.raises(ValueError):
            ConceptGraph(g)

    def test_prereqs_and_successors(self) -> None:
        g = nx.DiGraph()
        g.add_edges_from([(1, 2), (2, 3), (1, 3)])
        graph = ConceptGraph(g)
        # Note: 1→3 is pruned by transitive reduction inside build_concept_graph,
        # but ConceptGraph itself doesn't do that.
        assert graph.prerequisites(3) == [1, 2]
        assert graph.successors(1) == [2, 3]
        assert graph.prerequisites(1) == []

    def test_topological_next_picks_ready_concept(self) -> None:
        g = nx.DiGraph()
        g.add_edges_from([(1, 2), (2, 3)])
        graph = ConceptGraph(g)
        assert graph.topological_next(mastered=[]) == 1
        assert graph.topological_next(mastered=[1]) == 2
        assert graph.topological_next(mastered=[1, 2]) == 3
        assert graph.topological_next(mastered=[1, 2, 3]) is None

    def test_pickle_roundtrip(self, tmp_path: Path) -> None:
        g = nx.DiGraph()
        g.add_edges_from([(1, 2, {"ratio": 0.9, "support": 40})])
        g.add_node(3)
        original = ConceptGraph(g)
        path = original.save(tmp_path / "graph.pkl")
        assert path.exists()
        reloaded = ConceptGraph.load(path)
        assert set(reloaded.concepts()) == {1, 2, 3}
        assert reloaded.prerequisites(2) == [1]
        assert reloaded.graph[1][2]["ratio"] == 0.9


class TestBuildConceptGraph:
    def test_chain_skills_produce_expected_dag(self) -> None:
        # 30 students all do 1→2→3→4. Direct edges + transitive reduction.
        df = _chain_responses(n_students=30, chain=[1, 2, 3, 4])
        graph = build_concept_graph(
            df, min_overlap=20, order_threshold=0.7
        )
        assert set(graph.concepts()) == {1, 2, 3, 4}
        # After transitive reduction, expect exactly the chain.
        assert graph.prerequisites(2) == [1]
        assert graph.prerequisites(3) == [2]
        assert graph.prerequisites(4) == [3]

    def test_transitive_reduction_off(self) -> None:
        df = _chain_responses(n_students=30, chain=[1, 2, 3])
        graph = build_concept_graph(
            df,
            min_overlap=20,
            order_threshold=0.7,
            transitive_reduction=False,
        )
        assert graph.graph.has_edge(1, 3)  # kept when reduction off

    def test_low_overlap_yields_empty_graph(self) -> None:
        df = _chain_responses(n_students=5, chain=[1, 2, 3])
        graph = build_concept_graph(df, min_overlap=20)
        # Nodes still appear; no edges since overlap < 20.
        assert graph.graph.number_of_edges() == 0
        assert set(graph.concepts()) == {1, 2, 3}

    def test_untagged_excluded_from_nodes(self) -> None:
        df = _chain_responses(n_students=25, chain=[1, 2])
        df.loc[df["skill_id"] == 2, "skill_id"] = -1
        graph = build_concept_graph(df, min_overlap=20)
        assert -1 not in graph.concepts()

    def test_missing_column_raises(self) -> None:
        df = pd.DataFrame({"user_id": [0], "skill_id": [1]})
        with pytest.raises(KeyError):
            build_concept_graph(df)
