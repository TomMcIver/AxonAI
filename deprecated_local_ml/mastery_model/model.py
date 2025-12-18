"""
Mastery prediction model.
Logistic regression baseline with calibration support.
"""

import os
import json
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler


class MasteryModel:
    """Trainable mastery estimator outputting P(mastered)."""
    
    MODEL_DIR = 'models/mastery'
    
    def __init__(self, version: str = 'v1', use_online: bool = False):
        """
        Initialize mastery model.
        
        Args:
            version: Model version string
            use_online: If True, use SGDClassifier for online updates
        """
        self.version = version
        self.use_online = use_online
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        if use_online:
            self.model = SGDClassifier(
                loss='log_loss',
                penalty='l2',
                alpha=0.01,
                learning_rate='adaptive',
                eta0=0.1,
                warm_start=True,
                random_state=42
            )
        else:
            self.model = LogisticRegression(
                C=1.0,
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            )
        
        self.calibrator = None
        self.training_metrics = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray, 
            calibrate: bool = True) -> Dict:
        """
        Train the mastery model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (1=mastered, 0=not mastered)
            calibrate: Whether to apply probability calibration
            
        Returns:
            Dictionary of training metrics
        """
        X_scaled = self.scaler.fit_transform(X)
        
        if calibrate and len(X) >= 10:
            self.calibrator = CalibratedClassifierCV(
                self.model, 
                method='isotonic',
                cv=min(5, len(X) // 2)
            )
            self.calibrator.fit(X_scaled, y)
        else:
            self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        self.training_metrics = {
            'n_samples': len(y),
            'accuracy': np.mean(y_pred == y),
            'auc': self._calculate_auc(y, y_proba),
            'logloss': self._calculate_logloss(y, y_proba),
            'calibration_error': self._calculate_calibration_error(y, y_proba),
            'trained_at': datetime.utcnow().isoformat(),
            'version': self.version
        }
        
        return self.training_metrics
    
    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Online update for SGDClassifier.
        
        Args:
            X: Feature matrix
            y: Binary labels
        """
        if not self.use_online:
            raise ValueError("Model not configured for online learning")
        
        if not self.is_fitted:
            self.scaler.fit(X)
            self.model.classes_ = np.array([0, 1])
        
        X_scaled = self.scaler.transform(X)
        self.model.partial_fit(X_scaled, y, classes=[0, 1])
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict mastery (binary)."""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        X_scaled = self.scaler.transform(X)
        
        if self.calibrator is not None:
            return self.calibrator.predict(X_scaled)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict P(mastered)."""
        if not self.is_fitted:
            return np.full(len(X), 0.5)
        
        X_scaled = self.scaler.transform(X)
        
        if self.calibrator is not None:
            proba = self.calibrator.predict_proba(X_scaled)
        else:
            proba = self.model.predict_proba(X_scaled)
        
        return proba[:, 1]
    
    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        if path is None:
            os.makedirs(f'{self.MODEL_DIR}/{self.version}', exist_ok=True)
            path = f'{self.MODEL_DIR}/{self.version}/model.pkl'
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'calibrator': self.calibrator,
            'version': self.version,
            'use_online': self.use_online,
            'is_fitted': self.is_fitted,
            'training_metrics': self.training_metrics
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        metrics_path = path.replace('model.pkl', 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(self.training_metrics, f, indent=2)
        
        return path
    
    @classmethod
    def load(cls, path: str) -> 'MasteryModel':
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(
            version=model_data['version'],
            use_online=model_data['use_online']
        )
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.calibrator = model_data['calibrator']
        instance.is_fitted = model_data['is_fitted']
        instance.training_metrics = model_data['training_metrics']
        
        return instance
    
    @classmethod
    def load_latest(cls) -> Optional['MasteryModel']:
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
            return roc_auc_score(y_true, y_proba)
        except:
            return 0.5
    
    def _calculate_logloss(self, y_true: np.ndarray, y_proba: np.ndarray) -> float:
        """Calculate log loss."""
        try:
            from sklearn.metrics import log_loss
            eps = 1e-15
            y_proba = np.clip(y_proba, eps, 1 - eps)
            return log_loss(y_true, y_proba)
        except:
            return 1.0
    
    def _calculate_calibration_error(self, y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> float:
        """Calculate expected calibration error (ECE)."""
        try:
            bin_edges = np.linspace(0, 1, n_bins + 1)
            ece = 0.0
            
            for i in range(n_bins):
                mask = (y_proba >= bin_edges[i]) & (y_proba < bin_edges[i + 1])
                if np.sum(mask) > 0:
                    bin_accuracy = np.mean(y_true[mask])
                    bin_confidence = np.mean(y_proba[mask])
                    ece += np.abs(bin_accuracy - bin_confidence) * np.sum(mask) / len(y_true)
            
            return ece
        except:
            return 0.1
    
    def get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from model coefficients."""
        if not self.is_fitted or not hasattr(self.model, 'coef_'):
            return {}
        
        coefs = self.model.coef_.flatten()
        importance = dict(zip(feature_names, np.abs(coefs)))
        return dict(sorted(importance.items(), key=lambda x: -x[1]))
