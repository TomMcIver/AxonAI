"""
Risk inference service.
Provides real-time at-risk predictions and state updates.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from .feature_builder import RiskFeatureBuilder
from .model import RiskModel


class RiskInference:
    """Service for real-time at-risk prediction and state management."""
    
    def __init__(self, use_ml: bool = True):
        """
        Initialize risk inference service.
        
        Args:
            use_ml: If True, use ML model; otherwise fall back to thresholds
        """
        self.use_ml = use_ml
        self.feature_builder = RiskFeatureBuilder()
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the latest trained model."""
        if not self.use_ml:
            return
        
        try:
            self.model = RiskModel.load_latest()
            if self.model:
                print(f"Loaded risk model version: {self.model.version}")
        except Exception as e:
            print(f"Failed to load risk model: {e}")
            self.model = None
    
    def predict_risk(self, student_id: int, class_id: int,
                     mastery_history: List[Dict],
                     interactions: List[Dict],
                     quiz_attempts: List[Dict],
                     attendance_rate: Optional[float] = None) -> Dict:
        """
        Predict at-risk probability for a student.
        
        Args:
            student_id: Student ID
            class_id: Class ID
            mastery_history: Historical mastery states
            interactions: AI interaction records
            quiz_attempts: Quiz/test responses
            attendance_rate: Optional attendance percentage
            
        Returns:
            Dictionary with p_risk, top_drivers, and metadata
        """
        features = self.feature_builder.build_features(
            student_id, mastery_history, interactions, 
            quiz_attempts, attendance_rate
        )
        
        if self.model is not None and self.model.is_fitted:
            p_risk = float(self.model.predict_proba(features.reshape(1, -1))[0])
            explanations = self.model.explain_prediction(features.reshape(1, -1), top_k=5)
            drivers = explanations[0]['drivers']
        else:
            p_risk = self._threshold_risk(features)
            drivers = self._heuristic_drivers(features)
        
        risk_level = 'high' if p_risk >= 0.7 else 'medium' if p_risk >= 0.4 else 'low'
        
        return {
            'p_risk': round(p_risk, 4),
            'risk_level': risk_level,
            'top_drivers': drivers,
            'model_version': self.model.version if self.model else 'threshold'
        }
    
    def _threshold_risk(self, features) -> float:
        """Fallback threshold-based risk calculation."""
        mastery_slope = features[1]
        avg_mastery = features[2]
        engagement = features[5]
        days_inactive = features[9]
        quiz_avg = features[13]
        
        risk_score = 0.0
        
        if avg_mastery < 0.5:
            risk_score += 0.3
        if mastery_slope < -0.05:
            risk_score += 0.2
        if engagement < 0.4:
            risk_score += 0.15
        if days_inactive > 7:
            risk_score += 0.2
        if quiz_avg < 0.6:
            risk_score += 0.15
        
        return min(risk_score, 1.0)
    
    def _heuristic_drivers(self, features) -> List[Dict]:
        """Generate heuristic drivers when no ML model."""
        drivers = []
        
        feature_names = self.feature_builder.FEATURE_NAMES
        thresholds = {
            'mastery_slope_14d': (-0.05, 'Declining mastery over 2 weeks'),
            'avg_mastery': (0.5, 'Low average mastery'),
            'engagement_current': (0.4, 'Low engagement level'),
            'days_since_activity': (7, 'Inactivity for over a week'),
            'quiz_score_avg': (0.6, 'Below average quiz scores')
        }
        
        for i, name in enumerate(feature_names):
            if name in thresholds:
                threshold, description = thresholds[name]
                value = features[i]
                
                if name == 'days_since_activity':
                    if value > threshold:
                        drivers.append({
                            'feature': name,
                            'description': description,
                            'value': float(value),
                            'direction': 'increases_risk'
                        })
                else:
                    if value < threshold:
                        drivers.append({
                            'feature': name,
                            'description': description,
                            'value': float(value),
                            'direction': 'increases_risk'
                        })
        
        return drivers[:5]
    
    def update_risk_score(self, db, student_id: int, class_id: int,
                          mastery_history: List[Dict],
                          interactions: List[Dict],
                          quiz_attempts: List[Dict],
                          attendance_rate: Optional[float] = None) -> 'RiskScore':
        """
        Update risk score in database.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            mastery_history: Historical mastery states
            interactions: AI interaction records
            quiz_attempts: Quiz/test responses
            attendance_rate: Optional attendance percentage
            
        Returns:
            Updated RiskScore record
        """
        from models import RiskScore
        
        prediction = self.predict_risk(
            student_id, class_id, mastery_history,
            interactions, quiz_attempts, attendance_rate
        )
        
        score = RiskScore.query.filter_by(
            student_id=student_id,
            class_id=class_id
        ).first()
        
        if score is None:
            score = RiskScore(
                student_id=student_id,
                class_id=class_id
            )
            db.session.add(score)
        
        score.p_risk = prediction['p_risk']
        score.risk_level = prediction['risk_level']
        score.top_drivers_json = json.dumps(prediction['top_drivers'])
        score.model_version = prediction['model_version']
        score.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return score
    
    def get_class_risk_summary(self, db, class_id: int) -> Dict:
        """
        Get risk summary for an entire class.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID
            
        Returns:
            Dictionary with class-level risk statistics
        """
        from models import RiskScore, User
        
        scores = RiskScore.query.filter_by(class_id=class_id).all()
        
        if not scores:
            return {
                'total_students': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'avg_risk': 0.5,
                'at_risk_students': []
            }
        
        high_risk = [s for s in scores if s.risk_level == 'high']
        medium_risk = [s for s in scores if s.risk_level == 'medium']
        low_risk = [s for s in scores if s.risk_level == 'low']
        
        at_risk_students = []
        for s in high_risk + medium_risk[:5]:
            student = User.query.get(s.student_id)
            if student:
                drivers = json.loads(s.top_drivers_json) if s.top_drivers_json else []
                at_risk_students.append({
                    'student_id': s.student_id,
                    'name': student.get_full_name(),
                    'p_risk': s.p_risk,
                    'risk_level': s.risk_level,
                    'top_drivers': drivers[:3]
                })
        
        return {
            'total_students': len(scores),
            'high_risk_count': len(high_risk),
            'medium_risk_count': len(medium_risk),
            'low_risk_count': len(low_risk),
            'avg_risk': sum(s.p_risk for s in scores) / len(scores),
            'at_risk_students': at_risk_students
        }
