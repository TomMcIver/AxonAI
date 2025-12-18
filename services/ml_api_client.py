"""
ML API Client - HTTP client for external ML services.
Calls Render-hosted ML endpoints for mastery, risk, and bandit operations.
"""

import json
import os
import uuid
import logging
from typing import Dict, Optional, Any, List
from functools import wraps
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

ML_API_BASE_URL = os.environ.get("ML_API_BASE_URL", "")
AXON_SERVICE_KEY = os.environ.get("AXON_SERVICE_KEY", "")

INFERENCE_TIMEOUT = 5
TRAINING_TIMEOUT = 30
MAX_RETRIES = 2
BACKOFF_FACTOR = 0.5


class MLAPIError(Exception):
    """Exception for ML API errors."""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class MLAPIClient:
    """HTTP client for external ML services with retries and error handling."""
    
    def __init__(self, base_url: str = None, service_key: str = None):
        """
        Initialize ML API client.
        
        Args:
            base_url: ML API base URL (defaults to ML_API_BASE_URL env var)
            service_key: Service authentication key (defaults to AXON_SERVICE_KEY env var)
        """
        self.base_url = (base_url or ML_API_BASE_URL).rstrip('/')
        self.service_key = service_key or AXON_SERVICE_KEY
        self._session = None
        
        if not self.base_url:
            logger.warning("ML_API_BASE_URL not configured - ML API calls will fail")
        if not self.service_key:
            logger.warning("AXON_SERVICE_KEY not configured - ML API calls will fail")
    
    @property
    def session(self) -> requests.Session:
        """Get or create requests session with retry configuration."""
        if self._session is None:
            self._session = requests.Session()
            
            retry_strategy = Retry(
                total=MAX_RETRIES,
                backoff_factor=BACKOFF_FACTOR,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)
        
        return self._session
    
    def _get_headers(self, request_id: str = None) -> Dict[str, str]:
        """Get headers for API request."""
        req_id = request_id or str(uuid.uuid4())
        return {
            "Content-Type": "application/json",
            "X-AXON-KEY": self.service_key,
            "X-Request-ID": req_id
        }
    
    def _make_request(self, endpoint: str, body: Dict, 
                      timeout: int = INFERENCE_TIMEOUT,
                      request_id: str = None) -> Dict:
        """
        Make HTTP POST request to ML API.
        
        Args:
            endpoint: API endpoint path (e.g., '/mastery/predict')
            body: Request body as dictionary
            timeout: Request timeout in seconds
            request_id: Optional request ID for tracing
            
        Returns:
            Response body as dictionary
            
        Raises:
            MLAPIError: If request fails
        """
        if not self.base_url:
            raise MLAPIError("ML_API_BASE_URL not configured")
        if not self.service_key:
            raise MLAPIError("AXON_SERVICE_KEY not configured")
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(request_id)
        
        try:
            logger.debug(f"ML API request: {endpoint} with body keys: {list(body.keys())}")
            
            response = self.session.post(
                url,
                json=body,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code >= 400:
                error_body = response.text[:500]
                logger.error(f"ML API error {response.status_code}: {error_body}")
                raise MLAPIError(
                    f"ML API request to {endpoint} failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_body=error_body
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"ML API timeout: {endpoint}")
            raise MLAPIError(f"ML API request to {endpoint} timed out after {timeout}s")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"ML API connection error: {endpoint} - {e}")
            raise MLAPIError(f"ML API connection failed: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ML API request error: {endpoint} - {e}")
            raise MLAPIError(f"ML API request failed: {str(e)}")
    
    def health_check(self) -> Dict:
        """
        Check ML API health.
        
        Returns:
            Health status dictionary
        """
        if not self.base_url:
            return {"status": "unhealthy", "error": "ML_API_BASE_URL not configured"}
        
        try:
            url = f"{self.base_url}/health"
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def predict_mastery(self, student_id: int, skill: str, 
                        class_id: int = None,
                        request_id: str = None) -> Dict:
        """
        Predict mastery probability for student/skill pair.
        
        Args:
            student_id: Student ID
            skill: Skill identifier
            class_id: Optional class ID for context
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary with p_mastery, confidence, and metadata
        """
        body = {
            "student_id": student_id,
            "skill": skill
        }
        if class_id is not None:
            body["class_id"] = class_id
        
        return self._make_request("/mastery/predict", body, 
                                  timeout=INFERENCE_TIMEOUT, 
                                  request_id=request_id)
    
    def predict_risk(self, student_id: int, class_id: int,
                     request_id: str = None) -> Dict:
        """
        Predict at-risk probability for student in class.
        
        Args:
            student_id: Student ID
            class_id: Class ID
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary with p_risk, risk_level, and drivers
        """
        body = {
            "student_id": student_id,
            "class_id": class_id
        }
        
        return self._make_request("/risk/score", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)
    
    def select_strategy(self, student_id: int, class_id: int,
                        bandit_type: str = "linucb",
                        context: Dict = None,
                        request_id: str = None) -> Dict:
        """
        Select teaching strategy using contextual bandit.
        
        Args:
            student_id: Student ID
            class_id: Class ID
            bandit_type: Type of bandit ('linucb' or 'thompson')
            context: Optional context features
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary with strategy name and metadata
        """
        body = {
            "student_id": student_id,
            "class_id": class_id,
            "bandit_type": bandit_type
        }
        if context:
            body["context"] = context
        
        return self._make_request("/bandit/select", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)
    
    def update_bandit_reward(self, student_id: int, class_id: int,
                             strategy: str, reward: float,
                             context: Dict = None,
                             request_id: str = None) -> Dict:
        """
        Update bandit with observed reward.
        
        Args:
            student_id: Student ID
            class_id: Class ID
            strategy: Strategy that was used
            reward: Observed reward (0-1)
            context: Optional context features
            request_id: Optional request ID for tracing
            
        Returns:
            Acknowledgment dictionary
        """
        body = {
            "student_id": student_id,
            "class_id": class_id,
            "strategy": strategy,
            "reward": reward
        }
        if context:
            body["context"] = context
        
        return self._make_request("/bandit/update", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)
    
    def trigger_mastery_training(self, request_id: str = None) -> Dict:
        """
        Trigger mastery model retraining (admin only).
        
        Args:
            request_id: Optional request ID for tracing
            
        Returns:
            Training job status
        """
        return self._make_request("/mastery/train", {},
                                  timeout=TRAINING_TIMEOUT,
                                  request_id=request_id)
    
    def trigger_risk_training(self, request_id: str = None) -> Dict:
        """
        Trigger risk model retraining (admin only).
        
        Args:
            request_id: Optional request ID for tracing
            
        Returns:
            Training job status
        """
        return self._make_request("/risk/train", {},
                                  timeout=TRAINING_TIMEOUT,
                                  request_id=request_id)
    
    def get_mastery_profile(self, student_id: int, 
                            request_id: str = None) -> Dict:
        """
        Get complete mastery profile for a student.
        
        Args:
            student_id: Student ID
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary mapping skill -> mastery data
        """
        body = {"student_id": student_id}
        return self._make_request("/mastery/profile", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)
    
    def get_class_risk_summary(self, class_id: int,
                               request_id: str = None) -> Dict:
        """
        Get risk summary for entire class.
        
        Args:
            class_id: Class ID
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary with class risk statistics
        """
        body = {"class_id": class_id}
        return self._make_request("/risk/class-summary", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)
    
    def get_mastery_heatmap(self, class_id: int,
                            request_id: str = None) -> Dict:
        """
        Get mastery heatmap for class.
        
        Args:
            class_id: Class ID
            request_id: Optional request ID for tracing
            
        Returns:
            Dictionary with skill x student mastery data
        """
        body = {"class_id": class_id}
        return self._make_request("/mastery/heatmap", body,
                                  timeout=INFERENCE_TIMEOUT,
                                  request_id=request_id)


_ml_api_client = None

def get_ml_api_client() -> MLAPIClient:
    """Get or create global ML API client instance."""
    global _ml_api_client
    if _ml_api_client is None:
        _ml_api_client = MLAPIClient()
    return _ml_api_client


def is_ml_api_configured() -> bool:
    """Check if ML API is properly configured."""
    return bool(ML_API_BASE_URL and AXON_SERVICE_KEY)
