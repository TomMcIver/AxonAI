"""
Contextual Bandit Module - Adaptive strategy selection using LinUCB.
Replaces epsilon-greedy with contextual bandits that learn from student context.
"""

from .linucb import LinUCBBandit
from .context_builder import ContextBuilder
from .policy import BanditPolicy

__all__ = ['LinUCBBandit', 'ContextBuilder', 'BanditPolicy']
