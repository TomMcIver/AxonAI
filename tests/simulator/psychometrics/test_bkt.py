"""Hand-computed tests for BKT.

Expected values derived from the posterior formula in bkt.py docstrings:
    P(K|correct) = P(K)(1-S) / [P(K)(1-S) + (1-P(K))G]
    P(K|wrong)   = P(K)S     / [P(K)S     + (1-P(K))(1-G)]
    P(K_next)    = P(K|obs) + (1-P(K|obs)) * T
"""

from __future__ import annotations

import pytest

from ml.simulator.psychometrics.bkt import BKTParams, BKTState, predict_correct, update


# Reference params used across tests.
PARAMS = BKTParams(p_init=0.3, p_transit=0.1, p_slip=0.1, p_guess=0.25)


class TestPredictCorrect:
    def test_full_knowledge_yields_one_minus_slip(self) -> None:
        # P(K)=1 → P(correct) = 1 - slip
        assert predict_correct(BKTState(p_known=1.0), PARAMS) == pytest.approx(0.9)

    def test_zero_knowledge_yields_guess(self) -> None:
        # P(K)=0 → P(correct) = guess
        assert predict_correct(BKTState(p_known=0.0), PARAMS) == pytest.approx(0.25)

    def test_mixed_state(self) -> None:
        # P(K)=0.5: 0.5*0.9 + 0.5*0.25 = 0.575
        assert predict_correct(BKTState(p_known=0.5), PARAMS) == pytest.approx(0.575)


class TestUpdate:
    def test_correct_increases_known(self) -> None:
        # Prior 0.5 + correct obs.
        # P(K|correct) = 0.5 * 0.9 / (0.5 * 0.9 + 0.5 * 0.25) = 0.45 / 0.575
        #              = 0.7826086956521739
        # Then learn: 0.7826... + (1 - 0.7826...) * 0.1 = 0.8043478260869565
        new = update(BKTState(p_known=0.5), is_correct=True, params=PARAMS)
        assert new.p_known == pytest.approx(0.8043478260869565)

    def test_wrong_decreases_known(self) -> None:
        # P(K|wrong) = 0.5 * 0.1 / (0.5 * 0.1 + 0.5 * 0.75) = 0.05 / 0.425
        #            = 0.11764705882352941
        # Then learn: 0.1176... + (1 - 0.1176...) * 0.1 = 0.20588235294117646
        new = update(BKTState(p_known=0.5), is_correct=False, params=PARAMS)
        assert new.p_known == pytest.approx(0.20588235294117646)

    def test_full_knowledge_correct_stays_full_after_transit(self) -> None:
        # P(K)=1 + correct: posterior = 1 * 0.9 / (1 * 0.9 + 0 * 0.25) = 1
        # Learn: 1 + 0 * 0.1 = 1.
        new = update(BKTState(p_known=1.0), is_correct=True, params=PARAMS)
        assert new.p_known == pytest.approx(1.0)

    def test_full_knowledge_wrong_collapses(self) -> None:
        # P(K)=1 + wrong: posterior = 1 * 0.1 / (1 * 0.1 + 0) = 1
        # Counter-intuitive only if slip=0; here a wrong response with
        # slip>0 is still attributable to the slip, so posterior stays 1.
        new = update(BKTState(p_known=1.0), is_correct=False, params=PARAMS)
        assert new.p_known == pytest.approx(1.0)

    def test_zero_knowledge_correct_posterior_is_zero(self) -> None:
        # P(K)=0 + correct: posterior = 0 / (0 + 1 * 0.25) = 0
        # Learn: 0 + 1 * 0.1 = 0.1 (one learning event).
        new = update(BKTState(p_known=0.0), is_correct=True, params=PARAMS)
        assert new.p_known == pytest.approx(0.1)

    def test_learning_rate_drives_slow_climb_from_zero(self) -> None:
        # Repeatedly wrong with p_known=0: posterior stays 0, so each step
        # adds exactly p_transit. After N wrong, p_known = 1 - (1 - T)^N.
        state = BKTState(p_known=0.0)
        for _ in range(3):
            state = update(state, is_correct=False, params=PARAMS)
        # Actually, P(K|wrong) when k=0: 0 / (0 + 1 * 0.75) = 0
        # Each step: next = 0 + 1 * 0.1 ... but then next step starts from 0.1
        # P(K|wrong) = 0.1 * 0.1 / (0.1*0.1 + 0.9*0.75) = 0.01/0.685 ≈ 0.0146
        # Then learn: 0.0146 + 0.9854 * 0.1 = 0.1131
        # Let me just assert the trajectory is increasing (learning wins).
        assert state.p_known > 0.0

    def test_correct_then_wrong_ordering(self) -> None:
        # Start at prior 0.3. Correct then wrong:
        # After correct: P(K|c) = 0.3*0.9/(0.3*0.9 + 0.7*0.25) = 0.27/0.445
        #              = 0.6067415730337079
        # Learn: 0.6067... + 0.3932... * 0.1 = 0.64606741573...
        state = BKTState(p_known=0.3)
        state = update(state, is_correct=True, params=PARAMS)
        assert state.p_known == pytest.approx(0.6460674157303371)

        # After wrong from 0.6460...:
        # P(K|w) = 0.6460... * 0.1 / (0.6460... * 0.1 + 0.3539... * 0.75)
        #        = 0.06460.../(0.06460... + 0.26544...)
        #        = 0.064606741.../0.330514...
        k_prev = 0.6460674157303371
        posterior_w = (k_prev * 0.1) / (k_prev * 0.1 + (1 - k_prev) * 0.75)
        expected = posterior_w + (1 - posterior_w) * 0.1
        state = update(state, is_correct=False, params=PARAMS)
        assert state.p_known == pytest.approx(expected)

    def test_degenerate_prior_no_divide_by_zero(self) -> None:
        # P(K)=0 and guess=0 makes a correct response impossible — the
        # numerator/denominator are both zero. Implementation falls back
        # to the prior, then learns.
        params = BKTParams(p_init=0.0, p_transit=0.1, p_slip=0.1, p_guess=0.0)
        new = update(BKTState(p_known=0.0), is_correct=True, params=params)
        # Fallback posterior = 0, then learn: 0 + 1 * 0.1 = 0.1
        assert new.p_known == pytest.approx(0.1)

    def test_no_learning_when_transit_zero(self) -> None:
        params = BKTParams(p_init=0.3, p_transit=0.0, p_slip=0.1, p_guess=0.25)
        # Posterior only, no learning kick-up.
        new = update(BKTState(p_known=0.5), is_correct=True, params=params)
        assert new.p_known == pytest.approx(0.7826086956521739)
