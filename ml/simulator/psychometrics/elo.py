"""Elo rating for adaptive educational systems — Pelánek (2016).

Implemented in PR 3.

Planned API:
    expected(r_student, r_question) -> float
    update(r_student, r_question, actual: bool, k: float) -> (float, float)
    k_factor(attempts_so_far: int) -> float             # anneal K=40 → K=10 by attempt 30
"""
