"""
Training script for mastery model.
Builds dataset from DB, trains model, and saves artifacts.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_mastery_dataset(db, days_back: int = 90):
    """
    Build training dataset from database.
    
    Args:
        db: SQLAlchemy database instance
        days_back: How many days of data to include
        
    Returns:
        Tuple of (X features, y labels, metadata)
    """
    from models import AIInteraction, MiniTestResponse, MasteryState, User
    from mastery_model.feature_builder import MasteryFeatureBuilder
    
    feature_builder = MasteryFeatureBuilder()
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    
    students = User.query.filter_by(role='student').all()
    
    X_list = []
    y_list = []
    metadata = []
    
    for student in students:
        interactions = AIInteraction.query.filter(
            AIInteraction.user_id == student.id,
            AIInteraction.created_at >= cutoff
        ).order_by(AIInteraction.created_at).all()
        
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
        
        quizzes = MiniTestResponse.query.filter(
            MiniTestResponse.user_id == student.id,
            MiniTestResponse.completed_at >= cutoff
        ).all() if hasattr(MiniTestResponse, 'completed_at') else []
        
        quiz_dicts = [
            {
                'completed_at': getattr(q, 'completed_at', datetime.utcnow()),
                'score': q.score,
                'time_taken': q.time_taken,
                'skills_tested': getattr(q, 'skill_scores', '[]')
            }
            for q in quizzes
        ]
        
        mastery_states = MasteryState.query.filter_by(student_id=student.id).all()
        
        skills = set()
        for i in interaction_dicts:
            if i.get('sub_topic'):
                skills.add(i['sub_topic'])
        for s in mastery_states:
            skills.add(s.skill)
        
        for skill in skills:
            features = feature_builder.build_features(
                student.id, skill, interaction_dicts, quiz_dicts
            )
            
            state = next((s for s in mastery_states if s.skill == skill), None)
            if state:
                label = 1 if state.p_mastery >= 0.7 else 0
            else:
                skill_quizzes = [q for q in quiz_dicts if skill in str(q.get('skills_tested', ''))]
                if skill_quizzes:
                    avg_score = np.mean([q['score'] for q in skill_quizzes])
                    label = 1 if avg_score >= 0.7 else 0
                else:
                    continue
            
            X_list.append(features)
            y_list.append(label)
            metadata.append({'student_id': student.id, 'skill': skill})
    
    return np.array(X_list), np.array(y_list), metadata


def train_mastery_model(db=None, app=None, version: str = None):
    """
    Train mastery model from database data.
    
    Args:
        db: SQLAlchemy database instance
        app: Flask app for context
        version: Model version string (auto-generated if None)
        
    Returns:
        Training metrics dictionary
    """
    from mastery_model.model import MasteryModel
    from mastery_model.feature_builder import MasteryFeatureBuilder
    
    if version is None:
        version = datetime.utcnow().strftime('v%Y%m%d_%H%M%S')
    
    if db is None:
        from app import app as flask_app, db as flask_db
        app = flask_app
        db = flask_db
    
    with app.app_context():
        print(f"Building mastery dataset...")
        X, y, metadata = build_mastery_dataset(db)
        
        if len(X) < 10:
            print(f"Insufficient data: {len(X)} samples. Need at least 10.")
            X = np.random.randn(100, 18)
            y = (np.random.rand(100) > 0.5).astype(int)
            print("Using synthetic data for training...")
        
        print(f"Dataset: {len(X)} samples, {np.sum(y)} positive, {len(y) - np.sum(y)} negative")
        
        n = len(X)
        indices = np.arange(n)
        np.random.shuffle(indices)
        split = int(n * 0.8)
        
        train_idx = indices[:split]
        val_idx = indices[split:]
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)}")
        
        model = MasteryModel(version=version)
        train_metrics = model.fit(X_train, y_train, calibrate=True)
        
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
        
        feature_builder = MasteryFeatureBuilder()
        importance = model.get_feature_importance(feature_builder.get_feature_names())
        print("\nTop feature importance:")
        for name, imp in list(importance.items())[:5]:
            print(f"  {name}: {imp:.4f}")
        
        try:
            from models import ModelVersion
            mv = ModelVersion(
                model_type='mastery',
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
    train_mastery_model()
