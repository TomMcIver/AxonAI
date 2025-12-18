"""
Feature builder for risk prediction model.
Extracts features indicating student at-risk status.
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class RiskFeatureBuilder:
    """Build features for at-risk prediction."""
    
    FEATURE_NAMES = [
        'mastery_slope_7d',
        'mastery_slope_14d',
        'avg_mastery',
        'min_mastery',
        'engagement_trend',
        'engagement_current',
        'missed_attempts_rate',
        'low_accuracy_streak',
        'attendance_rate',
        'days_since_activity',
        'session_frequency',
        'time_of_day_variance',
        'topic_churn_rate',
        'quiz_score_avg',
        'quiz_score_trend',
        'interaction_count_7d',
        'interaction_count_14d',
        'negative_indicator_rate',
        'help_request_rate',
        'difficulty_mismatch'
    ]
    
    def __init__(self):
        self.feature_dim = len(self.FEATURE_NAMES)
    
    def build_features(self, student_id: int,
                       mastery_history: List[Dict],
                       interactions: List[Dict],
                       quiz_attempts: List[Dict],
                       attendance_rate: Optional[float] = None,
                       current_time: Optional[datetime] = None) -> np.ndarray:
        """
        Build feature vector for at-risk prediction.
        
        Args:
            student_id: Student ID
            mastery_history: Historical mastery states
            interactions: AI interaction records
            quiz_attempts: Quiz/test responses
            attendance_rate: Optional attendance percentage
            current_time: Current timestamp
            
        Returns:
            numpy array of features
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        features = np.zeros(self.feature_dim)
        
        features[0] = self._calculate_slope(mastery_history, 7)
        features[1] = self._calculate_slope(mastery_history, 14)
        
        if mastery_history:
            masteries = [m.get('p_mastery', 0.5) for m in mastery_history]
            features[2] = np.mean(masteries)
            features[3] = np.min(masteries)
        else:
            features[2] = 0.5
            features[3] = 0.5
        
        features[4], features[5] = self._calculate_engagement_features(interactions)
        features[6] = self._calculate_missed_attempts_rate(interactions)
        features[7] = self._calculate_low_accuracy_streak(interactions)
        features[8] = attendance_rate if attendance_rate is not None else 0.9
        
        if interactions:
            timestamps = [i.get('created_at') for i in interactions if i.get('created_at')]
            if timestamps:
                last_activity = max(timestamps)
                if isinstance(last_activity, datetime):
                    features[9] = (current_time - last_activity).days
        
        features[10] = self._calculate_session_frequency(interactions, 14)
        features[11] = self._calculate_time_variance(interactions)
        features[12] = self._calculate_topic_churn(interactions)
        
        if quiz_attempts:
            scores = [q.get('score', 0.5) for q in quiz_attempts]
            features[13] = np.mean(scores)
            features[14] = self._calculate_score_trend(scores)
        else:
            features[13] = 0.5
            features[14] = 0.0
        
        features[15] = self._count_recent_interactions(interactions, 7)
        features[16] = self._count_recent_interactions(interactions, 14)
        features[17] = self._calculate_negative_rate(interactions)
        features[18] = self._calculate_help_request_rate(interactions)
        features[19] = self._calculate_difficulty_mismatch(interactions, mastery_history)
        
        return features
    
    def _calculate_slope(self, history: List[Dict], days: int) -> float:
        """Calculate mastery slope over specified days."""
        if len(history) < 2:
            return 0.0
        
        recent = history[-min(len(history), days):]
        if len(recent) < 2:
            return 0.0
        
        values = [h.get('p_mastery', 0.5) for h in recent]
        x = np.arange(len(values))
        
        if len(values) < 2:
            return 0.0
        
        slope = np.polyfit(x, values, 1)[0]
        return float(slope)
    
    def _calculate_engagement_features(self, interactions: List[Dict]) -> tuple:
        """Calculate engagement trend and current level."""
        if not interactions:
            return 0.0, 0.5
        
        scores = [i.get('engagement_score', 0.5) for i in interactions]
        current = np.mean(scores[-5:]) if len(scores) >= 5 else np.mean(scores)
        
        if len(scores) < 4:
            trend = 0.0
        else:
            mid = len(scores) // 2
            first_half = np.mean(scores[:mid])
            second_half = np.mean(scores[mid:])
            trend = second_half - first_half
        
        return trend, current
    
    def _calculate_missed_attempts_rate(self, interactions: List[Dict]) -> float:
        """Calculate rate of missed/incomplete attempts."""
        if not interactions:
            return 0.0
        
        missed = sum(1 for i in interactions 
                     if i.get('success_indicator') is None or 
                     len(str(i.get('response', ''))) < 10)
        return missed / len(interactions)
    
    def _calculate_low_accuracy_streak(self, interactions: List[Dict]) -> int:
        """Calculate current streak of low accuracy attempts."""
        streak = 0
        for i in reversed(interactions):
            if i.get('success_indicator', False) is False:
                streak += 1
            else:
                break
        return streak
    
    def _calculate_session_frequency(self, interactions: List[Dict], days: int) -> float:
        """Calculate average sessions per day."""
        if not interactions:
            return 0.0
        
        dates = set()
        for i in interactions:
            ts = i.get('created_at')
            if isinstance(ts, datetime):
                dates.add(ts.date())
        
        return len(dates) / max(days, 1)
    
    def _calculate_time_variance(self, interactions: List[Dict]) -> float:
        """Calculate variance in time-of-day of interactions."""
        hours = []
        for i in interactions:
            ts = i.get('created_at')
            if isinstance(ts, datetime):
                hours.append(ts.hour)
        
        if len(hours) < 2:
            return 0.0
        
        return float(np.std(hours) / 12.0)
    
    def _calculate_topic_churn(self, interactions: List[Dict]) -> float:
        """Calculate rate of topic switching (high churn = unfocused)."""
        topics = [i.get('sub_topic', 'general') for i in interactions if i.get('sub_topic')]
        
        if len(topics) < 2:
            return 0.0
        
        switches = sum(1 for i in range(1, len(topics)) if topics[i] != topics[i-1])
        return switches / len(topics)
    
    def _calculate_score_trend(self, scores: List[float]) -> float:
        """Calculate trend in quiz scores."""
        if len(scores) < 2:
            return 0.0
        
        mid = len(scores) // 2
        first_half = np.mean(scores[:mid]) if mid > 0 else 0.5
        second_half = np.mean(scores[mid:]) if mid > 0 else 0.5
        
        return second_half - first_half
    
    def _count_recent_interactions(self, interactions: List[Dict], days: int) -> int:
        """Count interactions in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0
        for i in interactions:
            ts = i.get('created_at')
            if isinstance(ts, datetime) and ts > cutoff:
                count += 1
        return count
    
    def _calculate_negative_rate(self, interactions: List[Dict]) -> float:
        """Calculate rate of negative indicators in messages."""
        if not interactions:
            return 0.0
        
        negative_words = ['confused', 'stuck', 'lost', 'help', 'difficult', 
                          'hard', 'wrong', "don't understand", "don't get"]
        
        negative_count = 0
        for i in interactions:
            prompt = str(i.get('prompt', '')).lower()
            if any(w in prompt for w in negative_words):
                negative_count += 1
        
        return negative_count / len(interactions)
    
    def _calculate_help_request_rate(self, interactions: List[Dict]) -> float:
        """Calculate rate of explicit help requests."""
        if not interactions:
            return 0.0
        
        help_count = 0
        for i in interactions:
            prompt = str(i.get('prompt', '')).lower()
            if 'help' in prompt or 'hint' in prompt or 'explain again' in prompt:
                help_count += 1
        
        return help_count / len(interactions)
    
    def _calculate_difficulty_mismatch(self, interactions: List[Dict], 
                                        mastery_history: List[Dict]) -> float:
        """Calculate mismatch between difficulty and mastery."""
        if not interactions or not mastery_history:
            return 0.0
        
        avg_mastery = np.mean([m.get('p_mastery', 0.5) for m in mastery_history])
        
        difficulties = []
        for i in interactions:
            ctx = i.get('context_data', '{}')
            try:
                data = json.loads(ctx) if isinstance(ctx, str) else ctx or {}
                diff_map = {'easy': 0.3, 'medium': 0.5, 'hard': 0.7}
                difficulties.append(diff_map.get(data.get('difficulty', 'medium'), 0.5))
            except:
                difficulties.append(0.5)
        
        if not difficulties:
            return 0.0
        
        avg_difficulty = np.mean(difficulties)
        return abs(avg_difficulty - avg_mastery)
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return self.FEATURE_NAMES.copy()
