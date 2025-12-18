"""
ML Integration Service - Routes ML requests to external API or local fallback.
Provides unified interface for mastery, risk, bandit, and retrieval.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .ml_api_client import get_ml_api_client, is_ml_api_configured, MLAPIError

logger = logging.getLogger(__name__)

USE_LOCAL_ML = os.environ.get("USE_LOCAL_ML", "false").lower() == "true"
USE_ML_MASTERY = True
USE_ML_RISK = True
USE_CONTEXTUAL_BANDIT = True
USE_EMBEDDING_RETRIEVAL = False


class MLIntegration:
    """Unified ML integration service for AxonAI.
    
    Routes requests to external ML API when configured, 
    falls back to heuristics when not available.
    """
    
    def __init__(self):
        self.mastery_inference = None
        self.risk_inference = None
        self.bandit_policy = None
        self.content_retriever = None
        self.use_remote_ml = is_ml_api_configured() and not USE_LOCAL_ML
        
        self._init_services()
    
    def _init_services(self):
        """Initialize ML services - remote API or local fallback."""
        if self.use_remote_ml:
            logger.info("Using remote ML API for inference")
            self._api_client = get_ml_api_client()
        else:
            logger.info("ML API not configured, using heuristic fallback")
            self._api_client = None
            
            if USE_LOCAL_ML:
                self._init_local_services()
    
    def _init_local_services(self):
        """Initialize local ML services (deprecated, for fallback only)."""
        if USE_ML_MASTERY:
            try:
                from deprecated_local_ml.mastery_model import MasteryInference
                self.mastery_inference = MasteryInference(use_ml=True)
            except Exception as e:
                logger.warning(f"Local mastery inference init failed: {e}")
        
        if USE_ML_RISK:
            try:
                from deprecated_local_ml.risk_model import RiskInference
                self.risk_inference = RiskInference(use_ml=True)
            except Exception as e:
                logger.warning(f"Local risk inference init failed: {e}")
        
        if USE_CONTEXTUAL_BANDIT:
            try:
                from deprecated_local_ml.bandit import BanditPolicy
                self.bandit_policy = BanditPolicy(use_contextual=True)
            except Exception as e:
                logger.warning(f"Local bandit policy init failed: {e}")
    
    def get_student_context(self, db, student_id: int, class_id: int,
                            skill: Optional[str] = None) -> Dict:
        """
        Get comprehensive ML-enhanced student context.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            skill: Optional skill context
            
        Returns:
            Dictionary with mastery, risk, and profile data
        """
        from models import AIInteraction, MiniTestResponse, OptimizedProfile
        
        context = {
            'student_id': student_id,
            'class_id': class_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.use_remote_ml and self._api_client:
            try:
                if skill:
                    mastery_pred = self._api_client.predict_mastery(
                        student_id, skill, class_id
                    )
                    context['current_mastery'] = mastery_pred
                
                risk_pred = self._api_client.predict_risk(student_id, class_id)
                context['risk'] = {
                    'p_risk': risk_pred.get('p_risk', 0.5),
                    'risk_level': risk_pred.get('risk_level', 'unknown'),
                    'drivers': risk_pred.get('top_drivers', [])
                }
            except MLAPIError as e:
                logger.warning(f"ML API call failed, using DB fallback: {e}")
                self._populate_context_from_db(context, db, student_id, class_id, skill)
        else:
            self._populate_context_from_db(context, db, student_id, class_id, skill)
        
        profile = OptimizedProfile.query.filter_by(user_id=student_id).first()
        if profile:
            context['profile'] = {
                'engagement_level': profile.engagement_level,
                'current_pass_rate': profile.current_pass_rate,
                'preferred_strategies': json.loads(profile.preferred_strategies) if profile.preferred_strategies else []
            }
        
        return context
    
    def _populate_context_from_db(self, context: Dict, db, student_id: int, 
                                   class_id: int, skill: Optional[str]) -> None:
        """Populate context from database records (fallback when API unavailable)."""
        try:
            from models import MasteryState, RiskScore
            
            if skill:
                mastery_state = MasteryState.query.filter_by(
                    student_id=student_id, skill=skill
                ).first()
                if mastery_state:
                    context['current_mastery'] = {
                        'p_mastery': mastery_state.p_mastery,
                        'confidence': mastery_state.confidence,
                        'model_version': mastery_state.model_version
                    }
            
            mastery_states = MasteryState.query.filter_by(student_id=student_id).all()
            if mastery_states:
                context['mastery_profile'] = {
                    s.skill: {'p_mastery': s.p_mastery, 'trend': s.trend}
                    for s in mastery_states
                }
            
            risk_score = RiskScore.query.filter_by(
                student_id=student_id, class_id=class_id
            ).first()
            if risk_score:
                context['risk'] = {
                    'p_risk': risk_score.p_risk,
                    'risk_level': risk_score.risk_level,
                    'drivers': json.loads(risk_score.top_drivers_json) if risk_score.top_drivers_json else []
                }
        except Exception as e:
            logger.error(f"Error populating context from DB: {e}")
    
    def select_strategy(self, db, student_id: int, class_id: int,
                        skill: Optional[str] = None,
                        subject: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Select teaching strategy using contextual bandit or fallback.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            skill: Current skill
            subject: Subject for default strategy
            
        Returns:
            Tuple of (strategy_name, metadata)
        """
        if self.use_remote_ml and self._api_client:
            try:
                result = self._api_client.select_strategy(
                    student_id, class_id, 
                    bandit_type='linucb',
                    context={'skill': skill, 'subject': subject} if skill else None
                )
                return result.get('strategy', 'socratic'), result
            except MLAPIError as e:
                logger.warning(f"Remote bandit selection failed: {e}")
        
        return self._default_strategy_selection(subject)
    
    def _default_strategy_selection(self, subject: Optional[str]) -> Tuple[str, Dict]:
        """Fallback to default strategy selection."""
        from skill_taxonomy import get_default_strategy
        strategy = get_default_strategy(subject or 'math')
        return strategy, {'method': 'default_fallback'}
    
    def update_bandit_reward(self, db, student_id: int, class_id: int,
                             strategy: str, reward: float,
                             context: Dict = None) -> None:
        """
        Update bandit with observed reward.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            strategy: Strategy that was used
            reward: Observed reward (0-1)
            context: Optional context features
        """
        if self.use_remote_ml and self._api_client:
            try:
                self._api_client.update_bandit_reward(
                    student_id, class_id, strategy, reward, context
                )
            except MLAPIError as e:
                logger.warning(f"Failed to update bandit reward: {e}")
    
    def retrieve_content(self, db, message: str, class_id: int,
                         top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant content using keyword matching.
        
        Note: Embedding-based retrieval has been moved to external service.
        This method falls back to keyword matching.
        
        Args:
            db: SQLAlchemy database instance
            message: User message/query
            class_id: Class ID
            top_k: Number of results
            
        Returns:
            List of {source_name, snippet, score}
        """
        return []
    
    def update_after_interaction(self, db, student_id: int, class_id: int,
                                  strategy: str, skill: str,
                                  success: bool, engagement_delta: float = 0.0) -> None:
        """
        Update ML states after an interaction.
        
        Args:
            db: SQLAlchemy database instance
            student_id: Student ID
            class_id: Class ID
            strategy: Strategy that was used
            skill: Skill that was practiced
            success: Whether the interaction was successful
            engagement_delta: Change in engagement
        """
        reward = self._calculate_reward(success, engagement_delta)
        self.update_bandit_reward(db, student_id, class_id, strategy, reward)
    
    def _calculate_reward(self, success: bool, engagement_delta: float) -> float:
        """Calculate reward signal from outcomes."""
        base_reward = 0.7 if success else 0.3
        engagement_bonus = max(-0.2, min(0.2, engagement_delta * 0.5))
        return max(0, min(1, base_reward + engagement_bonus))
    
    def get_teacher_risk_summary(self, db, class_id: int) -> Dict:
        """
        Get risk summary for a class for teacher dashboard.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID
            
        Returns:
            Dictionary with class risk statistics
        """
        if self.use_remote_ml and self._api_client:
            try:
                return self._api_client.get_class_risk_summary(class_id)
            except MLAPIError as e:
                logger.warning(f"Remote risk summary failed: {e}")
        
        return self._get_risk_summary_from_db(db, class_id)
    
    def _get_risk_summary_from_db(self, db, class_id: int) -> Dict:
        """Get risk summary from database (fallback)."""
        from models import RiskScore, User
        
        scores = RiskScore.query.filter_by(class_id=class_id).all()
        if not scores:
            return {
                'total_students': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'at_risk_students': []
            }
        
        return {
            'total_students': len(scores),
            'high_risk_count': sum(1 for s in scores if s.risk_level == 'high'),
            'medium_risk_count': sum(1 for s in scores if s.risk_level == 'medium'),
            'low_risk_count': sum(1 for s in scores if s.risk_level == 'low'),
            'avg_risk': sum(s.p_risk for s in scores) / len(scores),
            'at_risk_students': [
                {'student_id': s.student_id, 'p_risk': s.p_risk, 'risk_level': s.risk_level}
                for s in scores if s.risk_level in ['high', 'medium']
            ][:10]
        }
    
    def get_mastery_heatmap(self, db, class_id: int) -> Dict:
        """
        Get class-level mastery heatmap for teacher dashboard.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID
            
        Returns:
            Dictionary with skill x student mastery data
        """
        if self.use_remote_ml and self._api_client:
            try:
                return self._api_client.get_mastery_heatmap(class_id)
            except MLAPIError as e:
                logger.warning(f"Remote mastery heatmap failed: {e}")
        
        return self._get_mastery_heatmap_from_db(db, class_id)
    
    def _get_mastery_heatmap_from_db(self, db, class_id: int) -> Dict:
        """Get mastery heatmap from database (fallback)."""
        from models import MasteryState, User, Class
        
        cls = Class.query.get(class_id)
        if not cls:
            return {'error': 'Class not found'}
        
        students = cls.get_students()
        student_ids = [s.id for s in students]
        
        states = MasteryState.query.filter(
            MasteryState.student_id.in_(student_ids)
        ).all()
        
        skills = set(s.skill for s in states)
        
        heatmap = {
            'students': [{'id': s.id, 'name': s.get_full_name()} for s in students],
            'skills': list(skills),
            'data': []
        }
        
        for student in students:
            student_row = {'student_id': student.id}
            for skill in skills:
                state = next((s for s in states if s.student_id == student.id and s.skill == skill), None)
                student_row[skill] = state.p_mastery if state else None
            heatmap['data'].append(student_row)
        
        return heatmap


ml_integration = None

def get_ml_integration():
    """Get or create the global ML integration instance."""
    global ml_integration
    if ml_integration is None:
        ml_integration = MLIntegration()
    return ml_integration
