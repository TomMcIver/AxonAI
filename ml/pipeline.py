"""
End-to-end training: load datasets from RDS, train models, upload joblib to S3,
write rows to model_predictions.

Run from repo root:
  python ml/pipeline.py

Requires AWS credentials with Secrets Manager + S3 access (local profile or IAM role).
"""

from __future__ import annotations

import io
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Any, Callable, Dict, FrozenSet, List, Tuple

_ML_ROOT = Path(__file__).resolve().parent
_ml_root_s = str(_ML_ROOT)
try:
    sys.path.remove(_ml_root_s)
except ValueError:
    pass
sys.path.insert(0, _ml_root_s)

import joblib
import numpy as np
import pandas as pd
import boto3
from psycopg2.extras import Json, execute_batch

from config import AWS_REGION, MIN_STUDENTS_TO_TRAIN, S3_BUCKET
from db import get_connection
from excluded_students import get_training_excluded_student_ids
from features import Dataset
from features.engagement import build_engagement_dataset
from features.mastery import build_mastery_dataset
from features.risk import build_risk_dataset
from features.teaching_strategy import build_strategy_dataset
from trainers.base import TrainResult
from trainers.engagement import train_engagement_regressor
from trainers.mastery import train_mastery_classifier
from trainers.risk import train_risk_classifier
from trainers.teaching_strategy import train_strategy_classifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAMES = {
    "mastery": "axonai_mastery_classifier",
    "risk": "axonai_risk_classifier",
    "engagement": "axonai_engagement_regressor",
    "teaching_strategy": "axonai_strategy_classifier",
}

PREDICTION_TYPES = {
    "mastery": "mastery_pass",
    "risk": "at_risk",
    "engagement": "engagement_score",
    "teaching_strategy": "strategy_success",
}

DATASET_BUILDERS = {
    "mastery": build_mastery_dataset,
    "risk": build_risk_dataset,
    "engagement": build_engagement_dataset,
    "teaching_strategy": build_strategy_dataset,
}


def _enough_students(features: pd.DataFrame) -> bool:
    if features.empty or "student_id" not in features.columns:
        return False
    return int(features["student_id"].nunique()) >= MIN_STUDENTS_TO_TRAIN


def _strategy_train_columns(cols: List[str]) -> List[str]:
    return [
        c
        for c in cols
        if c not in ("student_id", "pm_id")
        and not c.startswith("_meta")
    ]


def _aligned_training_matrix(
    feat_df: pd.DataFrame, train_cols: List[str]
) -> np.ndarray:
    """Ensure every training column exists (missing one-hot columns → 0)."""
    df = feat_df.copy()
    for c in train_cols:
        if c not in df.columns:
            df[c] = 0.0
    return df[train_cols].values.astype(np.float64)


def _train_matrix(
    ds: Dataset, model_type: str
) -> Tuple[np.ndarray, List[str], pd.DataFrame]:
    """Return X (numeric), column names used for training, full feature frame."""
    df = ds.features.copy()
    if model_type == "teaching_strategy":
        cols = _strategy_train_columns(list(df.columns))
    else:
        cols = [c for c in df.columns if c != "student_id"]
    X = df[cols].values.astype(np.float64)
    return X, cols, df


def _classifier_confidence(model: Any, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        return np.max(proba, axis=1)
    return np.ones(len(X), dtype=np.float64) * 0.85


def _upload_s3_artifact(payload: dict, key: str) -> None:
    buf = io.BytesIO()
    joblib.dump(payload, buf)
    buf.seek(0)
    boto3.client("s3", region_name=AWS_REGION).put_object(
        Bucket=S3_BUCKET, Key=key, Body=buf.getvalue()
    )
    logger.info("Uploaded s3://%s/%s", S3_BUCKET, key)


def _insert_predictions(
    rows: List[Tuple[Any, ...]],
) -> None:
    if not rows:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO model_predictions
                  (student_id, model_name, prediction_type, prediction_value,
                   confidence, input_features_snapshot)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb)
                """,
                rows,
                page_size=100,
            )
        conn.commit()
    finally:
        conn.close()
    logger.info("Inserted %s model_predictions rows", len(rows))


def run_training_step(
    model_type: str,
    train_fn: Callable[..., TrainResult],
    exclude_student_ids: FrozenSet[int],
) -> Dict[str, Any]:
    """Train one model on non-demo students; score demos as holdout if configured."""
    out: Dict[str, Any] = {
        "model_type": model_type,
        "status": "skipped",
        "holdout_rows_written": 0,
    }
    builder = DATASET_BUILDERS[model_type]
    ds = builder(exclude_student_ids=exclude_student_ids)
    if ds.features.empty or not _enough_students(ds.features):
        logger.warning(
            "Skipping %s: insufficient data (need >= %s distinct students).",
            model_type,
            MIN_STUDENTS_TO_TRAIN,
        )
        return out

    y = ds.labels.values
    X, train_cols, feat_df = _train_matrix(ds, model_type)

    result = train_fn(X, y, train_cols)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = {
        "model_type": model_type,
        "trained_at": ts,
        "feature_columns": result.feature_columns,
        "metrics": result.metrics,
        "model": result.model,
    }
    prefix = f"models/{model_type}"
    _upload_s3_artifact(artifact, f"{prefix}/latest/model.joblib")
    _upload_s3_artifact(artifact, f"{prefix}/{ts}/model.joblib")

    rows = _build_prediction_rows(
        model_type, result, X, train_cols, feat_df, ds, holdout_demo=False
    )
    _insert_predictions(rows)

    skip_holdout = (
        os.environ.get("AXONAI_ML_SKIP_HOLDOUT_INFERENCE", "").lower()
        in ("1", "true", "yes")
    )
    if exclude_student_ids and not skip_holdout:
        hold_n = _run_holdout_demo_inference(
            model_type, result, train_cols, exclude_student_ids
        )
        out["holdout_rows_written"] = hold_n

    out["status"] = "ok"
    out["metrics"] = result.metrics
    out["rows_written"] = len(rows)
    return out


def _run_holdout_demo_inference(
    model_type: str,
    result: TrainResult,
    train_cols: List[str],
    include_student_ids: FrozenSet[int],
) -> int:
    """
    Score frontend demo / excluded students using the model trained without them.
    """
    builder = DATASET_BUILDERS[model_type]
    ds_h = builder(include_only_student_ids=include_student_ids)
    if ds_h.features.empty:
        logger.info(
            "Holdout inference for %s: no rows for excluded student ids.",
            model_type,
        )
        return 0
    feat_df = ds_h.features.copy()
    Xh = _aligned_training_matrix(feat_df, train_cols)
    rows = _build_prediction_rows(
        model_type,
        result,
        Xh,
        train_cols,
        feat_df,
        ds_h,
        holdout_demo=True,
    )
    _insert_predictions(rows)
    logger.info(
        "Holdout inference for %s: wrote %s model_predictions rows.",
        model_type,
        len(rows),
    )
    return len(rows)


def _build_prediction_rows(
    model_type: str,
    result: TrainResult,
    X: np.ndarray,
    train_cols: List[str],
    feat_df: pd.DataFrame,
    ds: Dataset,
    *,
    holdout_demo: bool = False,
) -> List[Tuple[Any, ...]]:
    model = result.model
    name = MODEL_NAMES[model_type]
    ptype = PREDICTION_TYPES[model_type]
    rows: List[Tuple[Any, ...]] = []

    if model_type in ("mastery", "risk"):
        pred = model.predict(X)
        conf = _classifier_confidence(model, X)
        for i, sid in enumerate(feat_df["student_id"].values):
            pv = {
                "predicted_label": int(pred[i]),
                "probability": float(conf[i]),
            }
            if holdout_demo:
                pv["holdout_demo_inference"] = True
            snap = {c: _json_safe(X[i, j]) for j, c in enumerate(train_cols)}
            rows.append(
                (
                    int(sid),
                    name,
                    ptype,
                    Json(pv),
                    float(conf[i]),
                    Json(snap),
                )
            )

    elif model_type == "engagement":
        pred = model.predict(X)
        conf = np.ones(len(pred), dtype=np.float64) * 0.85
        y_true = ds.labels.values
        resid = np.abs(pred - y_true)
        conf = np.clip(1.0 - np.minimum(resid, 1.0), 0.0, 1.0)
        for i, sid in enumerate(feat_df["student_id"].values):
            pv = {"predicted_engagement": float(pred[i])}
            if holdout_demo:
                pv["holdout_demo_inference"] = True
            snap = {c: _json_safe(X[i, j]) for j, c in enumerate(train_cols)}
            rows.append(
                (
                    int(sid),
                    name,
                    ptype,
                    Json(pv),
                    float(conf[i]),
                    Json(snap),
                )
            )

    elif model_type == "teaching_strategy":
        pred = model.predict(X)
        conf = _classifier_confidence(model, X)
        for i in range(len(pred)):
            sid = int(feat_df["student_id"].iloc[i])
            pm_id = int(feat_df["pm_id"].iloc[i])
            pv = {
                "pedagogical_memory_id": pm_id,
                "predicted_success": int(pred[i]),
                "probability": float(conf[i]),
                "teaching_approach": str(
                    feat_df["_meta_teaching_approach"].iloc[i]
                ),
                "concept_type": str(feat_df["_meta_concept_type"].iloc[i]),
            }
            if holdout_demo:
                pv["holdout_demo_inference"] = True
            snap = {c: _json_safe(X[i, j]) for j, c in enumerate(train_cols)}
            rows.append(
                (
                    sid,
                    name,
                    ptype,
                    Json(pv),
                    float(conf[i]),
                    Json(snap),
                )
            )

    return rows


def _json_safe(v: Any) -> Any:
    if isinstance(v, (np.floating, float)):
        if np.isnan(v) or np.isinf(v):
            return None
        return float(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    return v


def run_pipeline() -> Dict[str, Any]:
    """Train all models; return summary."""
    summary: Dict[str, Any] = {"models": [], "bucket": S3_BUCKET}
    exclude = get_training_excluded_student_ids()
    summary["training_excluded_student_count"] = len(exclude)
    logger.info(
        "Excluding %s student id(s) from training (demo / is_demo_student / env).",
        len(exclude),
    )
    steps: List[Tuple[str, Callable[..., TrainResult]]] = [
        ("mastery", train_mastery_classifier),
        ("risk", train_risk_classifier),
        ("engagement", train_engagement_regressor),
        ("teaching_strategy", train_strategy_classifier),
    ]
    for mtype, trainer in steps:
        try:
            summary["models"].append(
                run_training_step(mtype, trainer, exclude)
            )
        except Exception:
            logger.exception("Training failed for %s", mtype)
            summary["models"].append({"model_type": mtype, "status": "error"})
    return summary


if __name__ == "__main__":
    result = run_pipeline()
    print(json.dumps(result, indent=2, default=str))
