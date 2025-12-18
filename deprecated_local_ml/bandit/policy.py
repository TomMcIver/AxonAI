"""
Bandit policy service for strategy selection.
Manages bandit state and provides strategy recommendations.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from skill_taxonomy import TEACHING_STRATEGIES, EPSILON, get_default_strategy
from .context_builder import ContextBuilder
from .linucb import LinUCBBandit, ThompsonSamplingBandit


USE_CONTEXTUAL_BANDIT = True


class BanditPolicy:
    """
    Policy service for adaptive strategy selection.
    Uses contextual bandit when enabled, falls back to epsilon-greedy.
    """
    
    STRATEGIES = TEACHING_STRATEGIES
    
    def __init__(self, use_contextual: bool = None, bandit_type: str = 'linucb'):
        """
        Initialize bandit policy.
        
        Args:
            use_contextual: Whether to use contextual bandit (default: USE_CONTEXTUAL_BANDIT)
            bandit_type: 'linucb' or 'thompson'
        """
        self.use_contextual = use_contextual if use_contextual is not None else USE_CONTEXTUAL_BANDIT
        self.bandit_type = bandit_type
        self.context_builder = ContextBuilder()
        
        self.n_arms = len(self.STRATEGIES)
        self.context_dim = self.context_builder.context_dim
        
        self.bandit = None
        self._load_or_init_bandit()
    
    def _load_or_init_bandit(self) -> None:
        """Load bandit state or initialize new one."""
        if not self.use_contextual:
            return
        
        if self.bandit_type == 'linucb':
            self.bandit = LinUCBBandit(
                n_arms=self.n_arms,
                context_dim=self.context_dim,
                alpha=1.0
            )
        else:
            self.bandit = ThompsonSamplingBandit(
                n_arms=self.n_arms,
                context_dim=self.context_dim
            )
    
    def select_strategy(self, student_id: int,
                        mastery_state: Optional[Dict] = None,
                        risk_state: Optional[Dict] = None,
                        profile: Optional[Dict] = None,
                        recent_interactions: Optional[List[Dict]] = None,
                        skill: Optional[str] = None,
                        subject: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Select teaching strategy for student.
        
        Args:
            student_id: Student ID
            mastery_state: Current mastery prediction
            risk_state: Current risk prediction
            profile: Optimized profile data
            recent_interactions: Recent AI interactions
            skill: Current skill
            subject: Subject for fallback
            
        Returns:
            Tuple of (strategy_name, metadata)
        """
        import random
        
        if not self.use_contextual or self.bandit is None:
            return self._epsilon_greedy_select(profile, skill, subject)
        
        context = self.context_builder.build_context(
            student_id=student_id,
            mastery_state=mastery_state,
            risk_state=risk_state,
            profile=profile,
            recent_interactions=recent_interactions,
            skill=skill
        )
        
        arm_idx, scores = self.bandit.select_arm(context)
        strategy = self.STRATEGIES[arm_idx]
        
        return strategy, {
            'method': self.bandit_type,
            'arm_index': arm_idx,
            'ucb_scores': scores.tolist(),
            'context': context.tolist()
        }
    
    def _epsilon_greedy_select(self, profile: Optional[Dict],
                               skill: Optional[str],
                               subject: Optional[str]) -> Tuple[str, Dict]:
        """Fallback epsilon-greedy selection."""
        import random
        
        if random.random() < EPSILON:
            strategy = random.choice(self.STRATEGIES)
            return strategy, {'method': 'epsilon_greedy', 'exploration': True}
        
        if profile and profile.get('strategy_success_rates'):
            try:
                rates = json.loads(profile['strategy_success_rates'])
                skill_stats = rates.get(skill or 'general', {})
                
                best_strategy = None
                best_rate = -1
                
                for strat, stats in skill_stats.items():
                    wins = stats.get('wins', 0)
                    trials = stats.get('trials', 0)
                    if trials > 0:
                        rate = wins / trials
                        if rate > best_rate:
                            best_rate = rate
                            best_strategy = strat
                
                if best_strategy:
                    return best_strategy, {'method': 'epsilon_greedy', 'exploitation': True}
            except:
                pass
        
        default = get_default_strategy(subject or 'math')
        return default, {'method': 'epsilon_greedy', 'default': True}
    
    def update_reward(self, student_id: int, strategy: str, reward: float,
                      context: Optional[List[float]] = None) -> None:
        """
        Update bandit with observed reward.
        
        Args:
            student_id: Student ID
            strategy: Strategy that was used
            reward: Observed reward (0-1, based on mastery gain or correctness)
            context: Context vector used for selection (optional)
        """
        if not self.use_contextual or self.bandit is None:
            return
        
        if strategy not in self.STRATEGIES:
            return
        
        arm_idx = self.STRATEGIES.index(strategy)
        
        if context is None:
            context = self.context_builder.build_context(student_id)
        else:
            context = np.array(context)
        
        self.bandit.update(arm_idx, context, reward)
    
    def save_state(self, db, student_id: int, class_id: int) -> None:
        """
        Save bandit state to database.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
        """
        from models import BanditPolicyState
        
        if self.bandit is None:
            return
        
        state = BanditPolicyState.query.filter_by(
            student_id=student_id,
            class_id=class_id
        ).first()
        
        if state is None:
            state = BanditPolicyState(
                student_id=student_id,
                class_id=class_id
            )
            db.session.add(state)
        
        state.policy_state_json = json.dumps(self.bandit.to_dict())
        state.bandit_type = self.bandit_type
        state.model_version = 'v1'
        state.updated_at = datetime.utcnow()
        
        db.session.commit()
    
    def load_state(self, db, student_id: int, class_id: int) -> bool:
        """
        Load bandit state from database.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            
        Returns:
            True if state was loaded, False otherwise
        """
        from models import BanditPolicyState
        
        state = BanditPolicyState.query.filter_by(
            student_id=student_id,
            class_id=class_id
        ).first()
        
        if state is None or not state.policy_state_json:
            return False
        
        try:
            data = json.loads(state.policy_state_json)
            
            if state.bandit_type == 'thompson':
                self.bandit = ThompsonSamplingBandit.from_dict(data)
            else:
                self.bandit = LinUCBBandit.from_dict(data)
            
            return True
        except Exception as e:
            print(f"Failed to load bandit state: {e}")
            return False
    
    def get_strategy_stats(self) -> Dict:
        """Get statistics for all strategies."""
        if self.bandit is None:
            return {'error': 'No bandit initialized'}
        
        arm_stats = self.bandit.get_arm_stats()
        
        return {
            'strategies': [
                {
                    'name': self.STRATEGIES[s['arm']],
                    **s
                }
                for s in arm_stats
            ],
            'bandit_type': self.bandit_type,
            'total_pulls': sum(s['count'] for s in arm_stats)
        }
    
    def calculate_reward(self, mastery_before: float, mastery_after: float,
                         correct: Optional[bool] = None,
                         engagement_delta: float = 0.0) -> float:
        """
        Calculate reward signal from outcomes.
        
        Primary: mastery gain
        Secondary: engagement change, correctness
        
        Args:
            mastery_before: Mastery before interaction
            mastery_after: Mastery after interaction
            correct: Whether the follow-up was correct
            engagement_delta: Change in engagement score
            
        Returns:
            Reward value (0-1)
        """
        mastery_gain = mastery_after - mastery_before
        
        mastery_reward = (mastery_gain + 0.1) / 0.2
        mastery_reward = max(0, min(1, mastery_reward))
        
        engagement_reward = (engagement_delta + 0.2) / 0.4
        engagement_reward = max(0, min(1, engagement_reward))
        
        correctness_reward = 1.0 if correct else 0.0 if correct is False else 0.5
        
        reward = 0.6 * mastery_reward + 0.25 * correctness_reward + 0.15 * engagement_reward
        
        return max(0, min(1, reward))


import numpy as np
