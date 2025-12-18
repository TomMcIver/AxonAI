"""
Roll-forward retraining script.
Schedules periodic retraining of models.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def roll_forward_retrain(db=None, app=None, min_new_interactions: int = 100):
    """
    Check if retraining is needed and retrain models.
    
    Args:
        db: SQLAlchemy database instance
        app: Flask app for context
        min_new_interactions: Minimum new interactions to trigger retrain
        
    Returns:
        Dictionary of retrain status
    """
    if db is None:
        from app import app as flask_app, db as flask_db
        app = flask_app
        db = flask_db
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'mastery': {'retrained': False},
        'risk': {'retrained': False}
    }
    
    with app.app_context():
        from models import AIInteraction, ModelVersion
        
        last_mastery = ModelVersion.query.filter_by(
            model_type='mastery', is_active=True
        ).order_by(ModelVersion.created_at.desc()).first()
        
        if last_mastery:
            last_train_time = last_mastery.created_at
            new_interactions = AIInteraction.query.filter(
                AIInteraction.created_at > last_train_time
            ).count()
        else:
            new_interactions = AIInteraction.query.count()
        
        print(f"New interactions since last training: {new_interactions}")
        
        if new_interactions >= min_new_interactions or last_mastery is None:
            print("Triggering mastery model retrain...")
            
            from training.train_mastery import train_mastery_model
            metrics = train_mastery_model(db, app)
            results['mastery'] = {
                'retrained': True,
                'metrics': metrics,
                'new_interactions': new_interactions
            }
        else:
            results['mastery'] = {
                'retrained': False,
                'reason': f'Only {new_interactions} new interactions (need {min_new_interactions})'
            }
        
        last_risk = ModelVersion.query.filter_by(
            model_type='risk', is_active=True
        ).order_by(ModelVersion.created_at.desc()).first()
        
        if new_interactions >= min_new_interactions or last_risk is None:
            print("Triggering risk model retrain...")
            
            from training.train_risk import train_risk_model
            metrics = train_risk_model(db, app)
            results['risk'] = {
                'retrained': True,
                'metrics': metrics
            }
        else:
            results['risk'] = {
                'retrained': False,
                'reason': 'Not enough new data'
            }
    
    log_path = 'models/retrain_log.json'
    os.makedirs('models', exist_ok=True)
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log = json.load(f)
    else:
        log = []
    
    log.append(results)
    log = log[-100:]
    
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"\nRetrain results: {json.dumps(results, indent=2)}")
    return results


if __name__ == '__main__':
    roll_forward_retrain()
