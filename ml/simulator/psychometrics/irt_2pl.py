"""Two-Parameter Logistic (2PL) IRT — Birnbaum (1968).

Pure functions; no data IO. Implemented in PR 3.

Planned API:
    prob_correct(theta: float, a: float, b: float) -> float
    sample_response(theta: float, a: float, b: float, rng) -> bool
    log_likelihood(responses, thetas, params) -> float
"""
