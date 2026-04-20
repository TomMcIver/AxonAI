"""Tests for the StudentGenerator.

Covers: schema, deterministic draws given a seed, prerequisite
correlation structure, fallback when priors/bkt_params are missing,
theta clamping.
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pytest

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.psychometrics.bkt import BKTParams
from ml.simulator.student.generator import StudentGenerator
from ml.simulator.student.misconceptions import SusceptibilitySampler


@pytest.fixture
def chain_graph() -> ConceptGraph:
    g = nx.DiGraph()
    g.add_edges_from([(1, 2), (2, 3), (3, 4)])
    return ConceptGraph(g)


@pytest.fixture
def priors() -> dict:
    return {
        "theta_mean": 0.0,
        "theta_std": 1.0,
        "slip_prior": {"mean": 0.1, "std": 0.02},
        "guess_prior": {"mean": 0.25, "std": 0.05},
        "learning_rate_lognorm": {"mu": math.log(0.1), "sigma": 0.2},
        "response_time_lognorm": {"mu": 9.0, "sigma": 0.4},
    }


@pytest.fixture
def bkt_params() -> dict:
    return {
        1: BKTParams(p_init=0.25, p_transit=0.15, p_slip=0.08, p_guess=0.2),
        2: BKTParams(p_init=0.3, p_transit=0.1, p_slip=0.1, p_guess=0.22),
    }


class TestDraw:
    def test_produces_all_graph_concepts(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(student_id=7, rng=np.random.default_rng(0))
        assert set(p.true_theta.keys()) == {1, 2, 3, 4}
        assert set(p.bkt_state.keys()) == {1, 2, 3, 4}
        assert set(p.recall_half_life.keys()) == {1, 2, 3, 4}
        assert p.student_id == 7

    def test_deterministic_given_seed(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p1 = gen.draw(0, np.random.default_rng(42))
        p2 = gen.draw(0, np.random.default_rng(42))
        assert p1.true_theta == p2.true_theta
        assert p1.learning_rate == p2.learning_rate
        assert p1.slip == p2.slip

    def test_bkt_state_uses_calibrated_p_init(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        assert p.bkt_state[1].p_known == pytest.approx(0.25)
        assert p.bkt_state[2].p_known == pytest.approx(0.3)

    def test_bkt_state_uses_default_for_missing_concept(
        self, chain_graph, priors, bkt_params
    ):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        # Concept 3 was not in bkt_params — falls back to _DEFAULT_BKT (0.2).
        assert p.bkt_state[3].p_known == pytest.approx(0.2)

    def test_slip_guess_within_bounds(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        for seed in range(20):
            p = gen.draw(seed, np.random.default_rng(seed))
            assert 0.0 <= p.slip <= 0.5
            assert 0.0 <= p.guess <= 0.5

    def test_theta_clamped_to_bounds(self, chain_graph, bkt_params):
        # Heavy-tailed theta_std would produce out-of-bound draws; clamp must hold.
        extreme = {
            "theta_mean": 0.0,
            "theta_std": 10.0,
            "learning_rate_lognorm": {"mu": math.log(0.1), "sigma": 0.0},
            "slip_prior": {"mean": 0.1, "std": 0.0},
            "guess_prior": {"mean": 0.25, "std": 0.0},
        }
        gen = StudentGenerator(priors=extreme, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(1))
        for t in p.true_theta.values():
            assert -4.0 <= t <= 4.0

    def test_correlation_along_prerequisites(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        thetas_1 = []
        thetas_2 = []
        for seed in range(500):
            p = gen.draw(seed, np.random.default_rng(seed))
            thetas_1.append(p.true_theta[1])
            thetas_2.append(p.true_theta[2])
        corr = np.corrcoef(thetas_1, thetas_2)[0, 1]
        # Expected rho ~ 0.6 * 1 + diffusion from base; should be clearly positive.
        assert corr > 0.4

    def test_uses_fallback_priors_when_absent(self, chain_graph, bkt_params):
        gen = StudentGenerator(priors={}, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        # With no learning_rate_lognorm, falls back to exp(log(0.1)) = 0.1.
        assert p.learning_rate == pytest.approx(0.1)

    def test_response_time_default_when_absent(self, chain_graph, bkt_params):
        priors_no_rt = {
            "theta_mean": 0.0, "theta_std": 1.0,
            "learning_rate_lognorm": {"mu": 0.0, "sigma": 0.0},
            "slip_prior": {"mean": 0.1, "std": 0.0},
            "guess_prior": {"mean": 0.25, "std": 0.0},
        }
        gen = StudentGenerator(priors=priors_no_rt, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        mu, sigma = p.response_time_lognorm_params
        assert mu == pytest.approx(math.log(10_000.0))
        assert sigma > 0.0

    def test_elo_starts_at_1200(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        assert p.elo_rating == 1200.0

    def test_history_and_last_retrieval_start_empty(self, chain_graph, priors, bkt_params):
        gen = StudentGenerator(priors=priors, concept_graph=chain_graph, bkt_params_by_concept=bkt_params)
        p = gen.draw(0, np.random.default_rng(0))
        assert p.attempts_history == []
        assert p.last_retrieval == {}

    def test_misconception_susceptibility_empty_without_sampler(
        self, chain_graph, priors, bkt_params
    ):
        gen = StudentGenerator(
            priors=priors,
            concept_graph=chain_graph,
            bkt_params_by_concept=bkt_params,
        )
        p = gen.draw(0, np.random.default_rng(0))
        assert p.misconception_susceptibility == {}

    def test_misconception_susceptibility_populated_with_sampler(
        self, chain_graph, priors, bkt_params
    ):
        catalogue = np.arange(200, dtype=np.int64)
        sampler = SusceptibilitySampler(misconception_ids=catalogue)
        gen = StudentGenerator(
            priors=priors,
            concept_graph=chain_graph,
            bkt_params_by_concept=bkt_params,
            susceptibility_sampler=sampler,
        )
        # Aggregate across seeds: at least one draw must be non-empty
        # (p(empty) = (1-r)^N → vanishingly small for N=200, r>0.02).
        any_non_empty = False
        for seed in range(5):
            p = gen.draw(seed, np.random.default_rng(seed))
            assert set(p.misconception_susceptibility).issubset(set(int(x) for x in catalogue))
            if p.misconception_susceptibility:
                any_non_empty = True
        assert any_non_empty

    def test_misconception_susceptibility_deterministic_with_sampler(
        self, chain_graph, priors, bkt_params
    ):
        catalogue = np.arange(200, dtype=np.int64)
        sampler = SusceptibilitySampler(misconception_ids=catalogue)
        gen = StudentGenerator(
            priors=priors,
            concept_graph=chain_graph,
            bkt_params_by_concept=bkt_params,
            susceptibility_sampler=sampler,
        )
        p1 = gen.draw(0, np.random.default_rng(7))
        p2 = gen.draw(0, np.random.default_rng(7))
        assert p1.misconception_susceptibility == p2.misconception_susceptibility
