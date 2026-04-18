"""Postgres writer — writes events to the production schema.

Implemented in PR 9. Every row is tagged is_simulated=True. A migration
is included in PR 9 to add the column where missing (non-negotiable).
"""
