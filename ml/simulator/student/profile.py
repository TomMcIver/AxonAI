"""StudentProfile dataclass.

Implemented in PR 7.

Planned fields:
    student_id
    true_theta:              dict[concept_id, float]   # ground truth, hidden
    estimated_theta:         dict[concept_id, tuple[float, float]]  # mean, var
    bkt_state:               dict[concept_id, BKTState]
    elo_rating:              float
    recall_half_life:        dict[concept_id, float]
    last_retrieval:          dict[concept_id, datetime]
    learning_rate, slip, guess, engagement_decay
    response_time_lognorm_params: tuple[float, float]
    attempts_history:        list[AttemptRecord]
    misconception_susceptibility: dict[misconception_id, float]  # empty in v1 (v2 seam)
"""
