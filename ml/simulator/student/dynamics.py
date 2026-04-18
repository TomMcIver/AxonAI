"""Student dynamics — pure functions.

Implemented in PR 7.

Planned API:
    apply_practice(profile, concept_id, is_correct) -> profile
        # bumps true θ, updates BKT, updates Elo
    apply_forgetting(profile, now: datetime) -> profile
        # decays true θ and HLR forward
"""
