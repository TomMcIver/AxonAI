"""Simulator v1 validation suite.

Phase 1 (this PR): self-consistency validation — generate a synthetic
ground truth with known IRT/BKT params, calibrate against its responses,
regenerate, and verify parameter recovery + distribution fidelity.

Phase 2 (follow-up, blocked on real data paths): cross-validation
against ASSISTments / Eedi / MAP responses. Same metrics, real inputs.
"""
