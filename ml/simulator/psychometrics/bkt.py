"""Bayesian Knowledge Tracing — Corbett & Anderson (1995).

Implemented in PR 3.

Planned API:
    BKTParams (dataclass): p_init, p_transit, p_slip, p_guess
    BKTState  (dataclass): p_known
    update(state, is_correct, params) -> BKTState       # Bayesian posterior
    predict_correct(state, params) -> float
"""
