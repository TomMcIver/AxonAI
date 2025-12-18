"""
LinUCB (Linear Upper Confidence Bound) contextual bandit implementation.
Selects strategies based on student context with exploration bonus.
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple


class LinUCBBandit:
    """
    LinUCB contextual bandit for adaptive strategy selection.
    
    Each arm (strategy) maintains its own linear model.
    Uses UCB exploration to balance exploration vs exploitation.
    """
    
    def __init__(self, n_arms: int, context_dim: int, alpha: float = 1.0):
        """
        Initialize LinUCB bandit.
        
        Args:
            n_arms: Number of arms (strategies)
            context_dim: Dimension of context vector
            alpha: Exploration parameter (higher = more exploration)
        """
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha
        
        self.A = [np.eye(context_dim) for _ in range(n_arms)]
        self.b = [np.zeros(context_dim) for _ in range(n_arms)]
        
        self.arm_counts = [0] * n_arms
        self.total_reward = [0.0] * n_arms
    
    def select_arm(self, context: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Select best arm given context using UCB.
        
        Args:
            context: Context vector (context_dim,)
            
        Returns:
            Tuple of (selected_arm_index, ucb_scores_for_all_arms)
        """
        ucb_scores = np.zeros(self.n_arms)
        
        for arm in range(self.n_arms):
            A_inv = np.linalg.inv(self.A[arm])
            theta = A_inv @ self.b[arm]
            
            expected_reward = context @ theta
            
            exploration_bonus = self.alpha * np.sqrt(context @ A_inv @ context)
            
            ucb_scores[arm] = expected_reward + exploration_bonus
        
        best_arm = np.argmax(ucb_scores)
        return int(best_arm), ucb_scores
    
    def update(self, arm: int, context: np.ndarray, reward: float) -> None:
        """
        Update arm parameters with observed reward.
        
        Args:
            arm: Arm index that was pulled
            context: Context vector used for selection
            reward: Observed reward (typically 0 or 1, or continuous)
        """
        self.A[arm] += np.outer(context, context)
        self.b[arm] += reward * context
        
        self.arm_counts[arm] += 1
        self.total_reward[arm] += reward
    
    def get_arm_stats(self) -> List[Dict]:
        """Get statistics for each arm."""
        stats = []
        for arm in range(self.n_arms):
            avg_reward = (self.total_reward[arm] / self.arm_counts[arm] 
                         if self.arm_counts[arm] > 0 else 0.0)
            
            theta = np.linalg.inv(self.A[arm]) @ self.b[arm]
            
            stats.append({
                'arm': arm,
                'count': self.arm_counts[arm],
                'total_reward': self.total_reward[arm],
                'avg_reward': avg_reward,
                'theta_norm': float(np.linalg.norm(theta))
            })
        return stats
    
    def to_dict(self) -> Dict:
        """Serialize bandit state to dictionary."""
        return {
            'n_arms': self.n_arms,
            'context_dim': self.context_dim,
            'alpha': self.alpha,
            'A': [a.tolist() for a in self.A],
            'b': [b.tolist() for b in self.b],
            'arm_counts': self.arm_counts,
            'total_reward': self.total_reward
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LinUCBBandit':
        """Deserialize bandit state from dictionary."""
        instance = cls(
            n_arms=data['n_arms'],
            context_dim=data['context_dim'],
            alpha=data.get('alpha', 1.0)
        )
        instance.A = [np.array(a) for a in data['A']]
        instance.b = [np.array(b) for b in data['b']]
        instance.arm_counts = data['arm_counts']
        instance.total_reward = data['total_reward']
        return instance


class ThompsonSamplingBandit:
    """
    Thompson Sampling with linear reward model.
    Alternative to LinUCB with Bayesian exploration.
    """
    
    def __init__(self, n_arms: int, context_dim: int, 
                 prior_var: float = 1.0, noise_var: float = 0.1):
        """
        Initialize Thompson Sampling bandit.
        
        Args:
            n_arms: Number of arms (strategies)
            context_dim: Dimension of context vector
            prior_var: Prior variance for weights
            noise_var: Observation noise variance
        """
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.prior_var = prior_var
        self.noise_var = noise_var
        
        self.B = [np.eye(context_dim) / prior_var for _ in range(n_arms)]
        self.mu = [np.zeros(context_dim) for _ in range(n_arms)]
        self.f = [np.zeros(context_dim) for _ in range(n_arms)]
        
        self.arm_counts = [0] * n_arms
    
    def select_arm(self, context: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Select arm by Thompson Sampling.
        
        Args:
            context: Context vector
            
        Returns:
            Tuple of (selected_arm_index, sampled_rewards)
        """
        sampled_rewards = np.zeros(self.n_arms)
        
        for arm in range(self.n_arms):
            cov = np.linalg.inv(self.B[arm])
            theta_sample = np.random.multivariate_normal(self.mu[arm], cov)
            sampled_rewards[arm] = context @ theta_sample
        
        best_arm = np.argmax(sampled_rewards)
        return int(best_arm), sampled_rewards
    
    def update(self, arm: int, context: np.ndarray, reward: float) -> None:
        """Update arm parameters with observed reward."""
        self.B[arm] += np.outer(context, context) / self.noise_var
        self.f[arm] += reward * context / self.noise_var
        
        cov = np.linalg.inv(self.B[arm])
        self.mu[arm] = cov @ self.f[arm]
        
        self.arm_counts[arm] += 1
    
    def to_dict(self) -> Dict:
        """Serialize bandit state."""
        return {
            'n_arms': self.n_arms,
            'context_dim': self.context_dim,
            'prior_var': self.prior_var,
            'noise_var': self.noise_var,
            'B': [b.tolist() for b in self.B],
            'mu': [m.tolist() for m in self.mu],
            'f': [f.tolist() for f in self.f],
            'arm_counts': self.arm_counts
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ThompsonSamplingBandit':
        """Deserialize bandit state."""
        instance = cls(
            n_arms=data['n_arms'],
            context_dim=data['context_dim'],
            prior_var=data.get('prior_var', 1.0),
            noise_var=data.get('noise_var', 0.1)
        )
        instance.B = [np.array(b) for b in data['B']]
        instance.mu = [np.array(m) for m in data['mu']]
        instance.f = [np.array(f) for f in data['f']]
        instance.arm_counts = data['arm_counts']
        return instance
