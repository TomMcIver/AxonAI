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


def train_mastery_model(db=None, app=None, version: str = None, regularization_strength: float = 1.0):
    """
    Train mastery model from database data with overfitting prevention.
    
    Args:
        db: SQLAlchemy database instance
        app: Flask app for context
        version: Model version string (auto-generated if None)
        regularization_strength: L2 regularization (C = 1/strength, higher = more regularization)
        
    Returns:
        Training metrics dictionary with training history for visualization
    """
    from mastery_model.model import MasteryModel
    from mastery_model.feature_builder import MasteryFeatureBuilder
    from sklearn.model_selection import cross_val_score
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    
    if version is None:
        version = datetime.utcnow().strftime('v%Y%m%d_%H%M%S')
    
    if db is None:
        from app import app as flask_app, db as flask_db
        app = flask_app
        db = flask_db
    
    training_history = {
        'train_loss': [],
        'val_loss': [],
        'train_accuracy': [],
        'val_accuracy': [],
        'epochs': []
    }
    
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
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val) if len(X_val) > 0 else X_val
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)}")
        
        C_value = 1.0 / regularization_strength
        
        max_iters = [50, 100, 200, 500, 1000]
        best_val_loss = float('inf')
        patience = 2
        patience_counter = 0
        best_model = None
        
        for i, max_iter in enumerate(max_iters):
            temp_model = LogisticRegression(
                C=C_value,
                penalty='l2',
                solver='lbfgs',
                max_iter=max_iter,
                warm_start=True,
                random_state=42
            )
            temp_model.fit(X_train_scaled, y_train)
            
            train_proba = temp_model.predict_proba(X_train_scaled)
            train_loss = -np.mean(
                y_train * np.log(train_proba[:, 1] + 1e-10) + 
                (1 - y_train) * np.log(train_proba[:, 0] + 1e-10)
            )
            train_accuracy = temp_model.score(X_train_scaled, y_train)
            
            if len(X_val) > 0:
                val_proba = temp_model.predict_proba(X_val_scaled)
                val_loss = -np.mean(
                    y_val * np.log(val_proba[:, 1] + 1e-10) + 
                    (1 - y_val) * np.log(val_proba[:, 0] + 1e-10)
                )
                val_accuracy = temp_model.score(X_val_scaled, y_val)
            else:
                val_loss = train_loss
                val_accuracy = train_accuracy
            
            training_history['epochs'].append(max_iter)
            training_history['train_loss'].append(float(train_loss))
            training_history['val_loss'].append(float(val_loss))
            training_history['train_accuracy'].append(float(train_accuracy))
            training_history['val_accuracy'].append(float(val_accuracy))
            
            print(f"Epoch {max_iter}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, train_acc={train_accuracy:.4f}, val_acc={val_accuracy:.4f}")
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model = temp_model
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {max_iter} (no improvement for {patience} rounds)")
                    break
        
        model = MasteryModel(version=version)
        model.model = best_model
        model.scaler = scaler
        
        train_metrics = {
            'accuracy': float(best_model.score(X_train_scaled, y_train)),
            'train_samples': len(y_train),
            'regularization_C': C_value
        }
        
        if len(X_val) > 0:
            y_val_pred = best_model.predict(X_val_scaled)
            val_metrics = {
                'val_accuracy': float(np.mean(y_val_pred == y_val)),
                'val_loss': float(best_val_loss),
                'val_samples': len(y_val)
            }
            train_metrics.update(val_metrics)
        
        train_metrics['training_history'] = training_history
        
        cv_scores = cross_val_score(
            LogisticRegression(C=C_value, penalty='l2', solver='lbfgs', max_iter=1000),
            scaler.fit_transform(X), y, cv=min(5, len(X) // 2), scoring='accuracy'
        )
        train_metrics['cv_accuracy_mean'] = float(np.mean(cv_scores))
        train_metrics['cv_accuracy_std'] = float(np.std(cv_scores))
        print(f"Cross-validation accuracy: {train_metrics['cv_accuracy_mean']:.4f} (+/- {train_metrics['cv_accuracy_std']:.4f})")
        
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
        
        print(f"\nTraining complete. Metrics: {json.dumps({k: v for k, v in train_metrics.items() if k != 'training_history'}, indent=2)}")
        return train_metrics


if __name__ == '__main__':
    train_mastery_model()
