"""
Feature builder for mastery model.
Extracts features from interaction + quiz data for mastery prediction.
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class MasteryFeatureBuilder:
    """Build features for mastery prediction from student interaction data."""
    
    FEATURE_NAMES = [
        'attempt_count',
        'correct_count', 
        'rolling_accuracy_5',
        'rolling_accuracy_10',
        'avg_difficulty',
        'avg_time_taken',
        'hint_usage_rate',
        'engagement_score_avg',
        'message_length_avg',
        'session_count',
        'days_since_first',
        'days_since_last',
        'recency_weight',
        'frequency_per_week',
        'streak_current',
        'streak_max',
        'improvement_trend',
        'consistency_score'
    ]
    
    def __init__(self):
        self.feature_dim = len(self.FEATURE_NAMES)
    
    def build_features(self, student_id: int, skill: str, 
                       interactions: List[Dict], 
                       quiz_attempts: List[Dict],
                       current_time: Optional[datetime] = None) -> np.ndarray:
        """
        Build feature vector for (student, skill) mastery prediction.
        
        Args:
            student_id: Student ID
            skill: Skill identifier (e.g., 'algebra', 'geometry')
            interactions: List of AIInteraction records as dicts
            quiz_attempts: List of quiz/mini-test responses as dicts
            current_time: Current timestamp (default: now)
            
        Returns:
            numpy array of features
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        features = np.zeros(self.feature_dim)
        
        skill_interactions = [i for i in interactions if i.get('sub_topic') == skill or skill == 'general']
        skill_quizzes = [q for q in quiz_attempts if skill in str(q.get('skills_tested', []))]
        
        all_attempts = self._merge_attempts(skill_interactions, skill_quizzes)
        
        if not all_attempts:
            return features
        
        features[0] = len(all_attempts)
        features[1] = sum(1 for a in all_attempts if a.get('correct', False))
        features[2] = self._rolling_accuracy(all_attempts, 5)
        features[3] = self._rolling_accuracy(all_attempts, 10)
        features[4] = np.mean([a.get('difficulty', 0.5) for a in all_attempts])
        features[5] = np.mean([a.get('time_taken', 60) for a in all_attempts]) / 60.0
        features[6] = sum(1 for a in all_attempts if a.get('hint_used', False)) / max(len(all_attempts), 1)
        features[7] = np.mean([a.get('engagement_score', 0.5) for a in all_attempts])
        features[8] = np.mean([a.get('message_length', 50) for a in all_attempts]) / 100.0
        
        session_dates = set(a.get('date') for a in all_attempts if a.get('date'))
        features[9] = len(session_dates)
        
        timestamps = [a.get('timestamp') for a in all_attempts if a.get('timestamp')]
        if timestamps:
            first_ts = min(timestamps)
            last_ts = max(timestamps)
            features[10] = (current_time - first_ts).days if isinstance(first_ts, datetime) else 0
            features[11] = (current_time - last_ts).days if isinstance(last_ts, datetime) else 0
            features[12] = np.exp(-features[11] / 7.0)
            features[13] = len(all_attempts) / max(features[10] / 7.0, 1.0)
        
        correct_seq = [1 if a.get('correct', False) else 0 for a in all_attempts]
        features[14], features[15] = self._calculate_streaks(correct_seq)
        features[16] = self._calculate_trend(correct_seq)
        features[17] = self._calculate_consistency(correct_seq)
        
        return features
    
    def _merge_attempts(self, interactions: List[Dict], quizzes: List[Dict]) -> List[Dict]:
        """Merge interactions and quiz attempts into unified attempt list."""
        attempts = []
        
        for i in interactions:
            attempts.append({
                'timestamp': i.get('created_at'),
                'date': i.get('created_at').date() if isinstance(i.get('created_at'), datetime) else None,
                'correct': i.get('success_indicator', False),
                'difficulty': self._parse_difficulty(i.get('context_data', '{}')),
                'time_taken': i.get('response_time_ms', 60000) / 1000,
                'hint_used': 'hint' in str(i.get('prompt', '')).lower(),
                'engagement_score': i.get('engagement_score', 0.5),
                'message_length': len(str(i.get('prompt', ''))),
                'type': 'interaction'
            })
        
        for q in quizzes:
            attempts.append({
                'timestamp': q.get('completed_at') or q.get('created_at'),
                'date': (q.get('completed_at') or q.get('created_at')).date() 
                        if isinstance(q.get('completed_at') or q.get('created_at'), datetime) else None,
                'correct': q.get('score', 0) >= 0.7,
                'difficulty': 0.5,
                'time_taken': q.get('time_taken', 300),
                'hint_used': False,
                'engagement_score': min(q.get('score', 0.5) + 0.2, 1.0),
                'message_length': 50,
                'type': 'quiz'
            })
        
        attempts.sort(key=lambda x: x.get('timestamp') or datetime.min)
        return attempts
    
    def _parse_difficulty(self, context_data: str) -> float:
        """Parse difficulty from context data JSON."""
        try:
            data = json.loads(context_data) if isinstance(context_data, str) else context_data or {}
            diff_map = {'easy': 0.3, 'medium': 0.5, 'hard': 0.7}
            return diff_map.get(data.get('difficulty', 'medium'), 0.5)
        except:
            return 0.5
    
    def _rolling_accuracy(self, attempts: List[Dict], window: int) -> float:
        """Calculate rolling accuracy over last N attempts."""
        if not attempts:
            return 0.5
        recent = attempts[-window:]
        correct = sum(1 for a in recent if a.get('correct', False))
        return correct / len(recent)
    
    def _calculate_streaks(self, correct_seq: List[int]) -> Tuple[int, int]:
        """Calculate current and max correct streaks."""
        if not correct_seq:
            return 0, 0
        
        max_streak = 0
        current_streak = 0
        
        for c in correct_seq:
            if c == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        final_streak = 0
        for c in reversed(correct_seq):
            if c == 1:
                final_streak += 1
            else:
                break
        
        return final_streak, max_streak
    
    def _calculate_trend(self, correct_seq: List[int]) -> float:
        """Calculate improvement trend (-1 to 1)."""
        if len(correct_seq) < 4:
            return 0.0
        
        mid = len(correct_seq) // 2
        first_half = np.mean(correct_seq[:mid]) if mid > 0 else 0.5
        second_half = np.mean(correct_seq[mid:]) if mid > 0 else 0.5
        
        return second_half - first_half
    
    def _calculate_consistency(self, correct_seq: List[int]) -> float:
        """Calculate consistency score (0 to 1)."""
        if len(correct_seq) < 2:
            return 0.5
        return 1.0 - np.std(correct_seq)
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return self.FEATURE_NAMES.copy()
