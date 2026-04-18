"""AxonAI Simulator v1 — principled math-only synthetic student simulator.

Generates synthetic student trajectories through the Teach → Revise → Quiz
pedagogical loop with psychometric grounding: 2PL IRT, BKT, Elo, HLR retention.

Modules:
    config:         SimulationConfig (frozen dataclass, single source of constants)
    psychometrics:  Pure response/mastery/rating/retention models
    data:           Dataset loaders, concept graph, item bank
    calibration:    Fit 2PL, BKT, and student priors on ASSISTments
    student:        Profile, generator (seeded), dynamics
    loop:           Teach / revise / quiz / runner
    io:             Postgres + local parquet writers
    cli:            python -m ml.simulator {calibrate, run, validate}

Determinism: given (config, seed, input data), output is byte-identical.
"""
