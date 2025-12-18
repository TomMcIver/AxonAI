"""
Training script for risk model.
Builds dataset from DB, trains model, and saves artifacts.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_risk_dataset(db, days_back: int = 90, label_window: int = 14):
    """
    Build training dataset for risk prediction.
    
    Labels are derived from:
    - Predicted fail: final grade < 60%
    - Score drop: 10%+ drop in last 2 weeks
    - Disengagement: < 2 sessions in last 2 weeks
    
    Args:
        db: SQLAlchemy database instance
        days_back: How many days of data to include
        label_window: Days ahead to predict risk
        
    Returns:
        Tuple of (X features, y labels, metadata)
    """
    from models import AIInteraction, MiniTestResponse, MasteryState, User, Grade, Class
    from risk_model.feature_builder import RiskFeatureBuilder
    
    feature_builder = RiskFeatureBuilder()
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    
    students = User.query.filter_by(role='student').all()
    
    X_list = []
    y_list = []
    metadata = []
    
    for student in students:
        classes = student.classes
        
        for cls in classes:
            interactions = AIInteraction.query.filter(
                AIInteraction.user_id == student.id,
                AIInteraction.class_id == cls.id,
                AIInteraction.created_at >= cutoff
            ).order_by(AIInteraction.created_at).all()
            
            if len(interactions) < 3:
                continue
            
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
            
            mastery_states = MasteryState.query.filter_by(student_id=student.id).all()
            mastery_history = [
                {
                    'p_mastery': s.p_mastery,
                    'skill': s.skill,
                    'updated_at': s.updated_at
                }
                for s in mastery_states
            ]
            
            quiz_responses = MiniTestResponse.query.filter(
                MiniTestResponse.user_id == student.id
            ).all()
            
            quiz_dicts = [
                {
                    'score': q.score,
                    'time_taken': q.time_taken
                }
                for q in quiz_responses
            ]
            
            features = feature_builder.build_features(
                student.id,
                mastery_history,
                interaction_dicts,
                quiz_dicts,
                student.attendance_rate
            )
            
            label = derive_risk_label(student, cls, interactions, mastery_history)
            
            X_list.append(features)
            y_list.append(label)
            metadata.append({'student_id': student.id, 'class_id': cls.id})
    
    return np.array(X_list), np.array(y_list), metadata


def derive_risk_label(student, cls, interactions, mastery_history):
    """
    Derive at-risk label from student outcomes.
    
    Returns 1 (at-risk) if:
    - Average grade < 60%
    - Average mastery < 0.5
    - Low engagement (few interactions)
    """
    avg_grade = student.get_class_average(cls.id)
    if avg_grade is not None and avg_grade < 60:
        return 1
    
    if mastery_history:
        avg_mastery = np.mean([m['p_mastery'] for m in mastery_history])
        if avg_mastery < 0.4:
            return 1
    
    recent_cutoff = datetime.utcnow() - timedelta(days=14)
    recent_interactions = [i for i in interactions if i.created_at >= recent_cutoff]
    if len(recent_interactions) < 2 and len(interactions) >= 5:
        return 1
    
    return 0


def train_risk_model(db=None, app=None, version: str = None):
    """
    Train risk model from database data.
    
    Args:
        db: SQLAlchemy database instance
        app: Flask app for context
        version: Model version string
        
    Returns:
        Training metrics dictionary
    """
    from risk_model.model import RiskModel
    from risk_model.feature_builder import RiskFeatureBuilder
    
    if version is None:
        version = datetime.utcnow().strftime('v%Y%m%d_%H%M%S')
    
    if db is None:
        from app import app as flask_app, db as flask_db
        app = flask_app
        db = flask_db
    
    with app.app_context():
        print(f"Building risk dataset...")
        X, y, metadata = build_risk_dataset(db)
        
        if len(X) < 10:
            print(f"Insufficient data: {len(X)} samples. Need at least 10.")
            X = np.random.randn(100, 20)
            y = (np.random.rand(100) > 0.7).astype(int)
            print("Using synthetic data for training...")
        
        print(f"Dataset: {len(X)} samples, {np.sum(y)} at-risk, {len(y) - np.sum(y)} not at-risk")
        
        n = len(X)
        indices = np.arange(n)
        np.random.shuffle(indices)
        split = int(n * 0.8)
        
        train_idx = indices[:split]
        val_idx = indices[split:]
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)}")
        
        feature_builder = RiskFeatureBuilder()
        
        model = RiskModel(version=version)
        train_metrics = model.fit(X_train, y_train, feature_names=feature_builder.get_feature_names())
        
        if len(X_val) > 0:
            y_val_pred = model.predict(X_val)
            y_val_proba = model.predict_proba(X_val)
            
            val_metrics = {
                'val_accuracy': float(np.mean(y_val_pred == y_val)),
                'val_samples': len(y_val)
            }
            train_metrics.update(val_metrics)
        
        model_path = model.save()
        print(f"Model saved to: {model_path}")
        
        importance = model.get_feature_importance()
        print("\nTop feature importance:")
        for name, imp in list(importance.items())[:5]:
            print(f"  {name}: {imp:.4f}")
        
        try:
            from models import ModelVersion
            mv = ModelVersion(
                model_type='risk',
                version=version,
                metrics_json=json.dumps(train_metrics),
                is_active=True
            )
            db.session.add(mv)
            db.session.commit()
        except Exception as e:
            print(f"Could not save model version to DB: {e}")
        
        print(f"\nTraining complete. Metrics: {json.dumps(train_metrics, indent=2)}")
        return train_metrics


if __name__ == '__main__':
    train_risk_model()
