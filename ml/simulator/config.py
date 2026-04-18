"""Frozen SimulationConfig dataclass — the single source of every constant.

No magic numbers are permitted elsewhere in the simulator. Each field is
annotated with the paper or dataset it derives from.

Filled in PR 2-skeleton: placeholder. Populated in PR 2 follow-up / PR 3
(psychometric bounds) and PR 9 (output target, CLI-facing config shape).

Planned fields (see docs/simulator_v1_plan.md §3):
    n_students, term_weeks, sessions_per_week, minutes_per_session,
    subject, seed, output_target,
    slip_range, guess_range, learning_rate_lognorm,
    hlr_half_life_prior, elo_k_schedule, zpd_band, mastery_threshold.
"""
