"""
Demo Data Simulator Module.
Generates realistic student cohorts and learning data for demos.
"""

from .student_generator import StudentGenerator
from .interaction_simulator import InteractionSimulator
from .cohort_builder import CohortBuilder

__all__ = ['StudentGenerator', 'InteractionSimulator', 'CohortBuilder']
