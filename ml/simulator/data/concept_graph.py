"""Concept graph derived empirically from ASSISTments response ordering.

ASSISTments 2009-2010 ships flat skill labels per row — the dataset has
no native prerequisite hierarchy. We reconstruct one by looking at
**temporal ordering** of a student's first encounter with each skill:

    For every pair of skills (a, b), among students who touched both,
    count how often skill `a` was encountered before skill `b`.

    If that ratio exceeds `ORDER_THRESHOLD` (default 0.7) *and* the
    overlap count is >= `MIN_OVERLAP` (default 20), emit the directed
    edge  a  →  b  (meaning: `a` is a prerequisite of `b`).

Cycles are possible under this rule, so after edge construction we break
cycles by removing the weakest-evidence edge in each cycle, then run a
transitive reduction to keep the graph minimal.

Output is a `ConceptGraph` wrapping a `networkx.DiGraph`; `.save()` and
`.load()` use pickle since the graph carries per-edge evidence we want
to preserve for diagnostics.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Iterable

import networkx as nx
import pandas as pd

# Minimum student overlap for a skill pair before we trust an ordering
# signal. 20 is conservative for the ASSISTments sample size.
MIN_OVERLAP = 20
# Fraction of overlapping students that must see `a` before `b` to
# justify a prerequisite edge. 0.7 follows the usual curriculum-mining
# literature (e.g. Chen et al. 2018 on EDM skill trees).
ORDER_THRESHOLD = 0.7
# Sentinel for untagged responses in the loader — excluded from the graph.
_UNTAGGED_SKILL_ID = -1


class ConceptGraph:
    """Directed acyclic graph of concept prerequisites."""

    def __init__(self, graph: nx.DiGraph) -> None:
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("ConceptGraph requires a DAG")
        self._g = graph

    @property
    def graph(self) -> nx.DiGraph:
        return self._g

    def concepts(self) -> list[int]:
        return sorted(self._g.nodes())

    def prerequisites(self, concept_id: int) -> list[int]:
        """Direct prerequisites (in-edges)."""
        if concept_id not in self._g:
            return []
        return sorted(self._g.predecessors(concept_id))

    def successors(self, concept_id: int) -> list[int]:
        """Direct successors (out-edges)."""
        if concept_id not in self._g:
            return []
        return sorted(self._g.successors(concept_id))

    def topological_next(self, mastered: Iterable[int]) -> int | None:
        """Return the next concept whose prereqs are all in `mastered`.

        Uses a stable topological order; returns None once everything
        reachable is mastered.
        """
        mastered_set = set(mastered)
        for concept in nx.topological_sort(self._g):
            if concept in mastered_set:
                continue
            prereqs = set(self._g.predecessors(concept))
            if prereqs.issubset(mastered_set):
                return concept
        return None

    def save(self, path: Path | str) -> Path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            pickle.dump(self._g, f)
        return out_path

    @classmethod
    def load(cls, path: Path | str) -> "ConceptGraph":
        with Path(path).open("rb") as f:
            g = pickle.load(f)
        return cls(g)


def _first_touch_per_skill(responses_df: pd.DataFrame) -> pd.DataFrame:
    """One row per (user, skill) with the earliest start_time."""
    if "start_time" not in responses_df.columns:
        raise KeyError("build_concept_graph requires a 'start_time' column")
    df = responses_df.dropna(subset=["start_time"])
    df = df[df["skill_id"] != _UNTAGGED_SKILL_ID]
    return (
        df.groupby(["user_id", "skill_id"], as_index=False)["start_time"]
        .min()
        .rename(columns={"start_time": "first_time"})
    )


def _pairwise_ordering_counts(
    first_touch: pd.DataFrame,
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    """Return (before_counts, overlap_counts) for every skill pair.

    before_counts[(a, b)]  = #students who touched a before b
    overlap_counts[(a, b)] = #students who touched both (a, b) and (b, a);
                             stored symmetrically, so use the canonical
                             (min, max) key.
    """
    before: dict[tuple[int, int], int] = {}
    overlap: dict[tuple[int, int], int] = {}
    for _, group in first_touch.groupby("user_id", sort=False):
        # Sort by time, then by skill_id to break ties deterministically.
        ordered = group.sort_values(["first_time", "skill_id"])
        skills = ordered["skill_id"].to_numpy()
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a = int(skills[i])
                b = int(skills[j])
                if a == b:
                    continue
                # a was touched first → a → b evidence.
                before[(a, b)] = before.get((a, b), 0) + 1
                key = (min(a, b), max(a, b))
                overlap[key] = overlap.get(key, 0) + 1
    return before, overlap


def _candidate_edges(
    before: dict[tuple[int, int], int],
    overlap: dict[tuple[int, int], int],
    min_overlap: int,
    order_threshold: float,
) -> list[tuple[int, int, float, int]]:
    """Build the candidate edge list sorted by evidence strength.

    Returns (a, b, ratio, support) tuples where `ratio` is the fraction
    of overlapping students who saw `a` before `b`, and `support` is
    that overlap count.
    """
    edges = []
    seen_pairs: set[tuple[int, int]] = set()
    for (a, b), n_ab in before.items():
        key = (min(a, b), max(a, b))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        support = overlap.get(key, 0)
        if support < min_overlap:
            continue
        n_ba = before.get((b, a), 0)
        ratio_ab = n_ab / support
        ratio_ba = n_ba / support
        if ratio_ab >= order_threshold and ratio_ab > ratio_ba:
            edges.append((a, b, ratio_ab, support))
        elif ratio_ba >= order_threshold and ratio_ba > ratio_ab:
            edges.append((b, a, ratio_ba, support))
    # Strongest evidence first: higher ratio wins, then higher support.
    edges.sort(key=lambda e: (-e[2], -e[3], e[0], e[1]))
    return edges


def _acyclic_from_ranked_edges(
    nodes: Iterable[int],
    edges: list[tuple[int, int, float, int]],
) -> nx.DiGraph:
    """Greedily add edges strongest-first, skipping any that create a cycle."""
    g = nx.DiGraph()
    g.add_nodes_from(sorted(nodes))
    for a, b, ratio, support in edges:
        g.add_edge(a, b, ratio=ratio, support=support)
        try:
            next(nx.simple_cycles(g))
            g.remove_edge(a, b)
        except StopIteration:
            continue
    return g


def build_concept_graph(
    responses_df: pd.DataFrame,
    min_overlap: int = MIN_OVERLAP,
    order_threshold: float = ORDER_THRESHOLD,
    transitive_reduction: bool = True,
) -> ConceptGraph:
    """Build a `ConceptGraph` from ASSISTments-style responses.

    Requires columns user_id, skill_id, start_time. Rows with
    `skill_id == -1` (untagged) are ignored.
    """
    needed = {"user_id", "skill_id", "start_time"}
    missing = needed - set(responses_df.columns)
    if missing:
        raise KeyError(
            f"build_concept_graph requires {needed}; missing {missing}"
        )

    first_touch = _first_touch_per_skill(responses_df)
    before, overlap = _pairwise_ordering_counts(first_touch)
    edges = _candidate_edges(before, overlap, min_overlap, order_threshold)
    nodes = first_touch["skill_id"].unique().tolist()
    g = _acyclic_from_ranked_edges(nodes, edges)

    if transitive_reduction and g.number_of_edges() > 0:
        # nx.transitive_reduction drops edge attributes, so restore them
        # from the original graph for the edges that survive.
        reduced = nx.transitive_reduction(g)
        reduced.add_nodes_from(g.nodes())
        for u, v in reduced.edges():
            reduced[u][v].update(g[u][v])
        g = reduced

    return ConceptGraph(g)
