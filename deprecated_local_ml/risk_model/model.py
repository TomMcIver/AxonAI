"""
Risk prediction model.
Predicts P(at_risk_next_14_days) with explainable drivers.
"""

import os
import json
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class RiskModel:
    """Risk prediction model with explanations."""
    
    MODEL_DIR = 'models/risk'
    
    def __init__(self, version: str = 'v1'):
        """
        Initialize risk model.
        
        Args:
            version: Model version string
        """
        self.version = version
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        self.model = LogisticRegression(
            C=0.5,
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
        
        self.training_metrics = {}
        self.feature_names = []
    
    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: Optional[List[str]] = None) -> Dict:
        """
        Train the risk model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (1=at_risk, 0=not_at_risk)
            feature_names: Optional list of feature names for explanations
            
        Returns:
            Dictionary of training metrics
        """
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        self.training_metrics = {
            'n_samples': len(y),
            'n_positive': int(np.sum(y)),
            'n_negative': int(np.sum(1 - y)),
            'accuracy': float(np.mean(y_pred == y)),
            'auc': self._calculate_auc(y, y_proba),
            'logloss': self._calculate_logloss(y, y_proba),
            'precision': self._calculate_precision(y, y_pred),
            'recall': self._calculate_recall(y, y_pred),
            'trained_at': datetime.utcnow().isoformat(),
            'version': self.version
        }
        
        return self.training_metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict at-risk status (binary)."""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict P(at_risk)."""
        if not self.is_fitted:
            return np.full(len(X), 0.5)
        
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)
        return proba[:, 1]
    
    def explain_prediction(self, X: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Get top drivers for predictions using coefficient analysis.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            top_k: Number of top drivers to return
            
        Returns:
            List of dictionaries with feature contributions for each sample
        """
        if not self.is_fitted:
            return [{'drivers': []} for _ in range(len(X))]
        
        X_scaled = self.scaler.transform(X)
        
        coefs = self.model.coef_.flatten()
        
        explanations = []
        for i in range(len(X_scaled)):
            contributions = X_scaled[i] * coefs
            
            sorted_idx = np.argsort(np.abs(contributions))[::-1][:top_k]
            
            drivers = []
            for idx in sorted_idx:
                drivers.append({
                    'feature': self.feature_names[idx] if idx < len(self.feature_names) else f'feature_{idx}',
                    'contribution': float(contributions[idx]),
                    'direction': 'increases_risk' if contributions[idx] > 0 else 'decreases_risk',
                    'value': float(X[i, idx])
                })
            
            explanations.append({'drivers': drivers})
        
        return explanations
    
    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        if path is None:
            os.makedirs(f'{self.MODEL_DIR}/{self.version}', exist_ok=True)
            path = f'{self.MODEL_DIR}/{self.version}/model.pkl'
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'version': self.version,
            'is_fitted': self.is_fitted,
            'training_metrics': self.training_metrics,
            'feature_names': self.feature_names
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        metrics_path = path.replace('model.pkl', 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(self.training_metrics, f, indent=2)
        
        return path
    
    @classmethod
    def load(cls, path: str) -> 'RiskModel':
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(version=model_data['version'])
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.is_fitted = model_data['is_fitted']
        instance.training_metrics = model_data['training_metrics']
        instance.feature_names = model_data.get('feature_names', [])
        
        return instance
    
    @classmethod
    def load_latest(cls) -> Optional['RiskModel']:
        """Load the latest version of the model."""
        if not os.path.exists(cls.MODEL_DIR):
            return None
        
        versions = sorted(os.listdir(cls.MODEL_DIR), reverse=True)
        for v in versions:
            path = f'{cls.MODEL_DIR}/{v}/model.pkl'
            if os.path.exists(path):
                return cls.load(path)
        return None
    
    def _calculate_auc(self, y_true: np.ndarray, y_proba: np.ndarray) -> float:
        """Calculate AUC-ROC."""
        try:
            from sklearn.metrics import roc_auc_score
            if len(np.unique(y_true)) < 2:
                return 0.5
            return float(roc_auc_score(y_true, y_proba))
        except:
            return 0.5
    
    def _calculate_logloss(self, y_true: np.ndarray, y_proba: np.ndarray) -> float:
        """Calculate log loss."""
        try:
            from sklearn.metrics import log_loss
            eps = 1e-15
            y_proba = np.clip(y_proba, eps, 1 - eps)
            return float(log_loss(y_true, y_proba))
        except:
            return 1.0
    
    def _calculate_precision(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate precision."""
        try:
            from sklearn.metrics import precision_score
            return float(precision_score(y_true, y_pred, zero_division=0))
        except:
            return 0.0
    
    def _calculate_recall(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate recall."""
        try:
            from sklearn.metrics import recall_score
            return float(recall_score(y_true, y_pred, zero_division=0))
        except:
            return 0.0
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from model coefficients."""
        if not self.is_fitted:
            return {}
        
        coefs = np.abs(self.model.coef_.flatten())
        importance = dict(zip(self.feature_names, coefs))
        return dict(sorted(importance.items(), key=lambda x: -x[1]))
