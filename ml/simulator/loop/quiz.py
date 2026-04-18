"""Quiz step — ZPD item selection and response simulation.

Implemented in PR 8.

Planned API:
    select_next_item(profile, item_bank, target_prob_range=(0.60, 0.85)) -> Item
    simulate_response(profile, item, rng) -> AttemptRecord

v1 response model: uses true_theta; wrong-answer distractor is uniformly
random. v2 replaces simulate_response with a misconception-weighted
variant — keep the seam single-function-clean.
"""
