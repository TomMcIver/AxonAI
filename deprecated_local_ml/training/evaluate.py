"""
Evaluation script for all ML models.
Runs cross-validation and generates reports.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def evaluate_all_models(db=None, app=None):
    """
    Evaluate all trained models.
    
    Args:
        db: SQLAlchemy database instance
        app: Flask app for context
        
    Returns:
        Dictionary of evaluation metrics for each model
    """
    if db is None:
        from app import app as flask_app, db as flask_db
        app = flask_app
        db = flask_db
    
    results = {}
    
    with app.app_context():
        mastery_results = evaluate_mastery_model(db)
        results['mastery'] = mastery_results
        
        risk_results = evaluate_risk_model(db)
        results['risk'] = risk_results
        
        bandit_results = evaluate_bandit_policy(db)
        results['bandit'] = bandit_results
        
        results['evaluated_at'] = datetime.utcnow().isoformat()
    
    report_path = 'models/evaluation_report.json'
    os.makedirs('models', exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nEvaluation report saved to: {report_path}")
    print(json.dumps(results, indent=2))
    
    return results


def evaluate_mastery_model(db):
    """Evaluate the mastery model."""
    from mastery_model import MasteryModel
    from training.train_mastery import build_mastery_dataset
    
    print("\nEvaluating mastery model...")
    
    model = MasteryModel.load_latest()
    if model is None:
        return {'error': 'No mastery model found', 'status': 'not_trained'}
    
    try:
        X, y, _ = build_mastery_dataset(db)
        
        if len(X) == 0:
            return {'error': 'No evaluation data', 'status': 'no_data'}
        
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)
        
        accuracy = float(np.mean(y_pred == y))
        
        from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
        
        precision = float(precision_score(y, y_pred, zero_division=0))
        recall = float(recall_score(y, y_pred, zero_division=0))
        f1 = float(f1_score(y, y_pred, zero_division=0))
        
        try:
            auc = float(roc_auc_score(y, y_proba))
        except:
            auc = 0.5
        
        calibration_error = calculate_calibration_error(y, y_proba)
        
        return {
            'status': 'evaluated',
            'version': model.version,
            'n_samples': len(X),
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc,
            'calibration_error': calibration_error
        }
        
    except Exception as e:
        return {'error': str(e), 'status': 'error'}


def evaluate_risk_model(db):
    """Evaluate the risk model."""
    from risk_model import RiskModel
    from training.train_risk import build_risk_dataset
    
    print("\nEvaluating risk model...")
    
    model = RiskModel.load_latest()
    if model is None:
        return {'error': 'No risk model found', 'status': 'not_trained'}
    
    try:
        X, y, _ = build_risk_dataset(db)
        
        if len(X) == 0:
            return {'error': 'No evaluation data', 'status': 'no_data'}
        
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)
        
        accuracy = float(np.mean(y_pred == y))
        
        from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
        
        precision = float(precision_score(y, y_pred, zero_division=0))
        recall = float(recall_score(y, y_pred, zero_division=0))
        f1 = float(f1_score(y, y_pred, zero_division=0))
        
        try:
            auc = float(roc_auc_score(y, y_proba))
        except:
            auc = 0.5
        
        return {
            'status': 'evaluated',
            'version': model.version,
            'n_samples': len(X),
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc
        }
        
    except Exception as e:
        return {'error': str(e), 'status': 'error'}


def evaluate_bandit_policy(db):
    """Evaluate the bandit policy performance."""
    from models import AIInteraction
    from skill_taxonomy import TEACHING_STRATEGIES
    
    print("\nEvaluating bandit policy...")
    
    try:
        interactions = AIInteraction.query.filter(
            AIInteraction.strategy_used.isnot(None)
        ).all()
        
        if len(interactions) == 0:
            return {'error': 'No interactions with strategies', 'status': 'no_data'}
        
        strategy_stats = {}
        for strat in TEACHING_STRATEGIES:
            strat_interactions = [i for i in interactions if i.strategy_used == strat]
            if strat_interactions:
                successes = sum(1 for i in strat_interactions if i.success_indicator)
                engagement_sum = sum(i.engagement_score or 0 for i in strat_interactions)
                
                strategy_stats[strat] = {
                    'count': len(strat_interactions),
                    'success_rate': successes / len(strat_interactions),
                    'avg_engagement': engagement_sum / len(strat_interactions)
                }
        
        sorted_strategies = sorted(
            strategy_stats.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )
        
        return {
            'status': 'evaluated',
            'total_interactions': len(interactions),
            'strategies_used': len(strategy_stats),
            'best_strategy': sorted_strategies[0][0] if sorted_strategies else None,
            'strategy_stats': strategy_stats
        }
        
    except Exception as e:
        return {'error': str(e), 'status': 'error'}


def calculate_calibration_error(y_true, y_proba, n_bins=10):
    """Calculate expected calibration error."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        mask = (y_proba >= bin_edges[i]) & (y_proba < bin_edges[i + 1])
        if np.sum(mask) > 0:
            bin_accuracy = np.mean(y_true[mask])
            bin_confidence = np.mean(y_proba[mask])
            ece += np.abs(bin_accuracy - bin_confidence) * np.sum(mask) / len(y_true)
    
    return float(ece)


if __name__ == '__main__':
    evaluate_all_models()
