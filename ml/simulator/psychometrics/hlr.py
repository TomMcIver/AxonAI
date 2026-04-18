"""Half-Life Regression retention — Settles & Meeder (2016), Duolingo.

Implemented in PR 3.

Planned API:
    predict_recall(half_life_hours, hours_since_last) -> float
    update_half_life(current_hl, is_correct, response_time_ms, features) -> float
"""
