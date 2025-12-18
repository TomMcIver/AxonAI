"""
Mastery inference service.
Provides real-time mastery predictions and state updates.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .feature_builder import MasteryFeatureBuilder
from .model import MasteryModel


class MasteryInference:
    """Service for real-time mastery prediction and state management."""
    
    def __init__(self, use_ml: bool = True):
        """
        Initialize mastery inference service.
        
        Args:
            use_ml: If True, use ML model; otherwise fall back to heuristics
        """
        self.use_ml = use_ml
        self.feature_builder = MasteryFeatureBuilder()
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the latest trained model."""
        if not self.use_ml:
            return
        
        try:
            self.model = MasteryModel.load_latest()
            if self.model:
                print(f"Loaded mastery model version: {self.model.version}")
        except Exception as e:
            print(f"Failed to load mastery model: {e}")
            self.model = None
    
    def predict_mastery(self, student_id: int, skill: str,
                        interactions: List[Dict],
                        quiz_attempts: List[Dict]) -> Dict:
        """
        Predict mastery probability for (student, skill).
        
        Args:
            student_id: Student ID
            skill: Skill identifier
            interactions: List of AI interactions
            quiz_attempts: List of quiz responses
            
        Returns:
            Dictionary with p_mastery, confidence, and features
        """
        features = self.feature_builder.build_features(
            student_id, skill, interactions, quiz_attempts
        )
        
        if self.model is not None and self.model.is_fitted:
            p_mastery = float(self.model.predict_proba(features.reshape(1, -1))[0])
        else:
            p_mastery = self._heuristic_mastery(features)
        
        confidence = self._calculate_confidence(features)
        
        return {
            'p_mastery': round(p_mastery, 4),
            'confidence': round(confidence, 4),
            'attempt_count': int(features[0]),
            'rolling_accuracy': round(float(features[2]), 4),
            'improvement_trend': round(float(features[16]), 4),
            'model_version': self.model.version if self.model else 'heuristic'
        }
    
    def _heuristic_mastery(self, features) -> float:
        """Fallback heuristic when no ML model is available."""
        attempt_count = features[0]
        rolling_acc = features[2]
        trend = features[16]
        consistency = features[17]
        
        if attempt_count == 0:
            return 0.5
        
        base_mastery = rolling_acc * 0.7 + consistency * 0.2 + max(0, trend) * 0.1
        
        if attempt_count < 3:
            base_mastery = base_mastery * 0.7 + 0.5 * 0.3
        
        return min(max(base_mastery, 0.0), 1.0)
    
    def _calculate_confidence(self, features) -> float:
        """Calculate confidence in the prediction."""
        attempt_count = features[0]
        
        if attempt_count == 0:
            return 0.1
        elif attempt_count < 3:
            return 0.3
        elif attempt_count < 10:
            return 0.6
        else:
            return 0.85
    
    def update_mastery_state(self, db, student_id: int, skill: str,
                             interactions: List[Dict],
                             quiz_attempts: List[Dict]) -> 'MasteryState':
        """
        Update mastery state in database after new interaction/quiz.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            skill: Skill identifier
            interactions: List of AI interactions
            quiz_attempts: List of quiz responses
            
        Returns:
            Updated MasteryState record
        """
        from models import MasteryState
        
        prediction = self.predict_mastery(student_id, skill, interactions, quiz_attempts)
        
        state = MasteryState.query.filter_by(
            student_id=student_id,
            skill=skill
        ).first()
        
        if state is None:
            state = MasteryState(
                student_id=student_id,
                skill=skill
            )
            db.session.add(state)
        
        state.p_mastery = prediction['p_mastery']
        state.confidence = prediction['confidence']
        state.model_version = prediction['model_version']
        state.attempt_count = prediction['attempt_count']
        state.rolling_accuracy = prediction['rolling_accuracy']
        state.trend = prediction['improvement_trend']
        state.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return state
    
    def get_student_mastery_profile(self, db, student_id: int) -> Dict[str, Dict]:
        """
        Get complete mastery profile for a student across all skills.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            
        Returns:
            Dictionary mapping skill -> mastery data
        """
        from models import MasteryState
        
        states = MasteryState.query.filter_by(student_id=student_id).all()
        
        profile = {}
        for state in states:
            profile[state.skill] = {
                'p_mastery': state.p_mastery,
                'confidence': state.confidence,
                'trend': state.trend,
                'attempt_count': state.attempt_count,
                'updated_at': state.updated_at.isoformat() if state.updated_at else None
            }
        
        return profile
    
    def batch_predict(self, student_skill_pairs: List[Tuple[int, str]],
                      interactions_by_student: Dict[int, List[Dict]],
                      quizzes_by_student: Dict[int, List[Dict]]) -> Dict:
        """
        Batch predict mastery for multiple (student, skill) pairs.
        
        Args:
            student_skill_pairs: List of (student_id, skill) tuples
            interactions_by_student: Dict mapping student_id -> interactions
            quizzes_by_student: Dict mapping student_id -> quiz attempts
            
        Returns:
            Dictionary mapping (student_id, skill) -> prediction
        """
        results = {}
        
        for student_id, skill in student_skill_pairs:
            interactions = interactions_by_student.get(student_id, [])
            quizzes = quizzes_by_student.get(student_id, [])
            
            prediction = self.predict_mastery(student_id, skill, interactions, quizzes)
            results[(student_id, skill)] = prediction
        
        return results
    
    def online_update(self, student_id: int, skill: str,
                      correct: bool, difficulty: float = 0.5) -> None:
        """
        Perform online model update after a new observation.
        Only works if model was initialized with use_online=True.
        
        Args:
            student_id: Student ID
            skill: Skill identifier
            correct: Whether the attempt was correct
            difficulty: Difficulty level of the attempt
        """
        if self.model is None or not self.model.use_online:
            return
        
        features = self.feature_builder.build_features(
            student_id, skill, [], []
        )
        
        features[0] += 1
        if correct:
            features[1] += 1
        
        import numpy as np
        self.model.partial_fit(
            features.reshape(1, -1),
            np.array([1 if correct else 0])
        )
