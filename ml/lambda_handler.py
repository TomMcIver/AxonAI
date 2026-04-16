"""
AWS Lambda entry point (EventBridge cron or manual invoke).

Set handler to `lambda_handler.handler` with deployment package rooted at `ml/`
(or adjust PYTHONPATH so `pipeline` imports resolve).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_ML_ROOT = Path(__file__).resolve().parent
_ml_root_s = str(_ML_ROOT)
try:
    sys.path.remove(_ml_root_s)
except ValueError:
    pass
sys.path.insert(0, _ml_root_s)

from pipeline import run_pipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler; runs full training pipeline."""
    _ = (event, context)
    try:
        result = run_pipeline()
        return {
            "statusCode": 200,
            "body": json.dumps(result, default=str),
        }
    except Exception:
        logger.exception("Pipeline failed")
        raise
