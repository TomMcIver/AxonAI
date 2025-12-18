"""
Context builder for contextual bandit.
Builds context vectors from student state for strategy selection.
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional


class ContextBuilder:
    """Build context vectors for contextual bandit strategy selection."""
    
    CONTEXT_FEATURES = [
        'mastery_level',
        'risk_level',
        'engagement_score',
        'difficulty_preference',
        'time_of_day',
        'session_length',
        'recent_accuracy',
        'streak_length',
        'topic_familiarity',
        'help_request_rate'
    ]
    
    def __init__(self):
        self.context_dim = len(self.CONTEXT_FEATURES)
    
    def build_context(self, student_id: int,
                      mastery_state: Optional[Dict] = None,
                      risk_state: Optional[Dict] = None,
                      profile: Optional[Dict] = None,
                      recent_interactions: Optional[List[Dict]] = None,
                      skill: Optional[str] = None,
                      current_time: Optional[datetime] = None) -> np.ndarray:
        """
        Build context vector for strategy selection.
        
        Args:
            student_id: Student ID
            mastery_state: Current mastery state from MasteryInference
            risk_state: Current risk state from RiskInference
            profile: OptimizedProfile data
            recent_interactions: Recent AI interactions
            skill: Current skill being worked on
            current_time: Current timestamp
            
        Returns:
            numpy array context vector
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        context = np.zeros(self.context_dim)
        
        if mastery_state:
            context[0] = mastery_state.get('p_mastery', 0.5)
        else:
            context[0] = 0.5
        
        if risk_state:
            risk_level_map = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
            context[1] = risk_level_map.get(risk_state.get('risk_level', 'medium'), 0.5)
        else:
            context[1] = 0.5
        
        if profile:
            context[2] = profile.get('engagement_level', 0.5)
            
            difficulty_map = {'easy': 0.3, 'medium': 0.5, 'hard': 0.7}
            context[3] = difficulty_map.get(
                profile.get('preferred_difficulty', 'medium'), 0.5
            )
        else:
            context[2] = 0.5
            context[3] = 0.5
        
        hour = current_time.hour
        if 6 <= hour < 12:
            context[4] = 0.3
        elif 12 <= hour < 18:
            context[4] = 0.5
        else:
            context[4] = 0.7
        
        if recent_interactions:
            first = recent_interactions[0].get('created_at')
            last = recent_interactions[-1].get('created_at')
            if isinstance(first, datetime) and isinstance(last, datetime):
                session_minutes = (last - first).total_seconds() / 60
                context[5] = min(session_minutes / 60.0, 1.0)
            
            correct = sum(1 for i in recent_interactions if i.get('success_indicator'))
            context[6] = correct / len(recent_interactions)
            
            streak = 0
            for i in reversed(recent_interactions):
                if i.get('success_indicator'):
                    streak += 1
                else:
                    break
            context[7] = min(streak / 5.0, 1.0)
            
            skill_interactions = sum(1 for i in recent_interactions 
                                    if i.get('sub_topic') == skill)
            context[8] = min(skill_interactions / 10.0, 1.0)
            
            help_count = sum(1 for i in recent_interactions 
                            if 'help' in str(i.get('prompt', '')).lower())
            context[9] = help_count / len(recent_interactions)
        
        return context
    
    def get_context_names(self) -> List[str]:
        """Return list of context feature names."""
        return self.CONTEXT_FEATURES.copy()
