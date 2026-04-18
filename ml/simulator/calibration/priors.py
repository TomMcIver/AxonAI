"""Derive student-trait priors from calibrated parameters + empirical trajectories.

Implemented in PR 5.

Draws on:
    - ASSISTments responses (implied θ distribution per student)
    - fit_2pl outputs (item_params)
    - fit_bkt outputs (slip/guess priors per skill)

Output: data/processed/student_priors.json with:
    theta_percentiles, learning_rate_lognorm, slip_prior, guess_prior,
    response_time_lognorm_params.
"""
