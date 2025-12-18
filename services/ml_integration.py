"""
ML Integration Service - Integrates all ML components into the live system.
Provides unified interface for mastery, risk, bandit, and retrieval.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

USE_ML_MASTERY = True
USE_ML_RISK = True
USE_CONTEXTUAL_BANDIT = True
USE_EMBEDDING_RETRIEVAL = True


class MLIntegration:
    """Unified ML integration service for AxonAI."""
    
    def __init__(self):
        self.mastery_inference = None
        self.risk_inference = None
        self.bandit_policy = None
        self.content_retriever = None
        
        self._init_services()
    
    def _init_services(self):
        """Initialize ML services with fallback."""
        if USE_ML_MASTERY:
            try:
                from mastery_model import MasteryInference
                self.mastery_inference = MasteryInference(use_ml=True)
            except Exception as e:
                print(f"Mastery inference init failed: {e}")
        
        if USE_ML_RISK:
            try:
                from risk_model import RiskInference
                self.risk_inference = RiskInference(use_ml=True)
            except Exception as e:
                print(f"Risk inference init failed: {e}")
        
        if USE_CONTEXTUAL_BANDIT:
            try:
                from bandit import BanditPolicy
                self.bandit_policy = BanditPolicy(use_contextual=True)
            except Exception as e:
                print(f"Bandit policy init failed: {e}")
        
        if USE_EMBEDDING_RETRIEVAL:
            try:
                from retrieval import ContentRetriever
                self.content_retriever = ContentRetriever(use_embeddings=True)
            except Exception as e:
                print(f"Content retriever init failed: {e}")
    
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
        from models import AIInteraction, MiniTestResponse, MasteryState, RiskScore, OptimizedProfile
        
        context = {
            'student_id': student_id,
            'class_id': class_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        interactions = AIInteraction.query.filter_by(
            user_id=student_id, class_id=class_id
        ).order_by(AIInteraction.created_at.desc()).limit(50).all()
        
        interaction_dicts = [
            {
                'created_at': i.created_at,
                'sub_topic': i.sub_topic,
                'success_indicator': i.success_indicator,
                'engagement_score': i.engagement_score,
                'response_time_ms': i.response_time_ms,
                'context_data': i.context_data,
                'prompt': i.prompt,
                'strategy_used': i.strategy_used
            }
            for i in interactions
        ]
        
        mastery_states = MasteryState.query.filter_by(student_id=student_id).all()
        
        if self.mastery_inference and skill:
            quiz_responses = MiniTestResponse.query.filter_by(user_id=student_id).all()
            quiz_dicts = [
                {'score': q.score, 'time_taken': q.time_taken, 'skills_tested': q.skill_scores}
                for q in quiz_responses
            ]
            
            mastery_pred = self.mastery_inference.predict_mastery(
                student_id, skill, interaction_dicts, quiz_dicts
            )
            context['current_mastery'] = mastery_pred
        else:
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
        elif self.risk_inference:
            mastery_history = [
                {'p_mastery': s.p_mastery, 'skill': s.skill, 'updated_at': s.updated_at}
                for s in mastery_states
            ]
            risk_pred = self.risk_inference.predict_risk(
                student_id, class_id, mastery_history, interaction_dicts, []
            )
            context['risk'] = risk_pred
        
        profile = OptimizedProfile.query.filter_by(user_id=student_id).first()
        if profile:
            context['profile'] = {
                'engagement_level': profile.engagement_level,
                'current_pass_rate': profile.current_pass_rate,
                'preferred_strategies': json.loads(profile.preferred_strategies) if profile.preferred_strategies else []
            }
        
        return context
    
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
        if self.bandit_policy is None:
            from skill_taxonomy import get_default_strategy
            return get_default_strategy(subject or 'math'), {'method': 'default'}
        
        context = self.get_student_context(db, student_id, class_id, skill)
        
        mastery_state = context.get('current_mastery', {})
        risk_state = context.get('risk', {})
        profile = context.get('profile', {})
        
        from models import AIInteraction
        recent = AIInteraction.query.filter_by(
            user_id=student_id, class_id=class_id
        ).order_by(AIInteraction.created_at.desc()).limit(10).all()
        
        recent_dicts = [
            {
                'created_at': i.created_at,
                'sub_topic': i.sub_topic,
                'success_indicator': i.success_indicator,
                'engagement_score': i.engagement_score
            }
            for i in recent
        ]
        
        return self.bandit_policy.select_strategy(
            student_id=student_id,
            mastery_state=mastery_state,
            risk_state=risk_state,
            profile=profile,
            recent_interactions=recent_dicts,
            skill=skill,
            subject=subject
        )
    
    def retrieve_content(self, db, message: str, class_id: int,
                         top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant content using embeddings or keyword fallback.
        
        Args:
            db: SQLAlchemy database instance
            message: User message/query
            class_id: Class ID
            top_k: Number of results
            
        Returns:
            List of {source_name, snippet, score}
        """
        if self.content_retriever is None:
            return []
        
        return self.content_retriever.retrieve(message, class_id, top_k, db)
    
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
        from models import AIInteraction, MasteryState
        
        if self.mastery_inference:
            interactions = AIInteraction.query.filter_by(
                user_id=student_id, class_id=class_id
            ).order_by(AIInteraction.created_at.desc()).limit(50).all()
            
            interaction_dicts = [
                {
                    'created_at': i.created_at,
                    'sub_topic': i.sub_topic,
                    'success_indicator': i.success_indicator,
                    'engagement_score': i.engagement_score,
                    'response_time_ms': i.response_time_ms,
                    'context_data': i.context_data,
                    'prompt': i.prompt
                }
                for i in interactions
            ]
            
            try:
                self.mastery_inference.update_mastery_state(
                    db, student_id, skill, interaction_dicts, []
                )
            except Exception as e:
                print(f"Mastery state update failed: {e}")
        
        if self.bandit_policy:
            old_state = MasteryState.query.filter_by(
                student_id=student_id, skill=skill
            ).first()
            
            mastery_before = old_state.p_mastery if old_state else 0.5
            
            new_state = MasteryState.query.filter_by(
                student_id=student_id, skill=skill
            ).first()
            mastery_after = new_state.p_mastery if new_state else mastery_before
            
            reward = self.bandit_policy.calculate_reward(
                mastery_before, mastery_after, success, engagement_delta
            )
            
            context = self.get_student_context(db, student_id, class_id, skill)
            
            try:
                self.bandit_policy.update_reward(
                    student_id, strategy, reward,
                    context=None
                )
            except Exception as e:
                print(f"Bandit update failed: {e}")
    
    def get_teacher_risk_summary(self, db, class_id: int) -> Dict:
        """
        Get risk summary for a class for teacher dashboard.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID
            
        Returns:
            Dictionary with class risk statistics
        """
        if self.risk_inference:
            return self.risk_inference.get_class_risk_summary(db, class_id)
        
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
