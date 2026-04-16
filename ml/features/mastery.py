"""Mastery pass/fail feature set (student-level)."""

from __future__ import annotations

from typing import AbstractSet, Optional

import numpy as np
import pandas as pd

from db import get_connection

from . import Dataset
from .student_filters import filter_dataset_by_students


def build_mastery_dataset(
    *,
    exclude_student_ids: Optional[AbstractSet[int]] = None,
    include_only_student_ids: Optional[AbstractSet[int]] = None,
) -> Dataset:
    """
    Features: avg quiz score %, mastery avg/min, evidence avg, lightbulb rate,
    conversation resolve rate, total_interactions.
    Label: 1 if avg mastery_score >= 0.65 else 0; median split if all on one side.
    """
    conn = get_connection()
    try:
        mastery = pd.read_sql(
            """
            SELECT student_id,
                   AVG(mastery_score) AS mastery_avg,
                   MIN(mastery_score) AS mastery_min,
                   AVG(evidence_count::float) AS evidence_avg
            FROM concept_mastery_states
            GROUP BY student_id
            """,
            conn,
        )
        quizzes = pd.read_sql(
            """
            SELECT student_id, AVG(score_percentage) AS quiz_score_avg
            FROM quiz_sessions
            WHERE score_percentage IS NOT NULL
            GROUP BY student_id
            """,
            conn,
        )
        conv = pd.read_sql(
            """
            SELECT student_id,
                   AVG(CASE WHEN lightbulb_moment_detected THEN 1.0 ELSE 0.0 END)
                       AS lightbulb_rate,
                   AVG(CASE WHEN outcome IN ('resolved', 'partially_resolved')
                       THEN 1.0 ELSE 0.0 END) AS resolve_rate
            FROM conversations
            GROUP BY student_id
            """,
            conn,
        )
        interactions = pd.read_sql(
            """
            SELECT student_id, COALESCE(total_interactions, 0) AS total_interactions
            FROM student_learning_profiles
            """,
            conn,
        )
    finally:
        conn.close()

    df = mastery.merge(quizzes, on="student_id", how="left")
    df = df.merge(conv, on="student_id", how="left")
    df = df.merge(interactions, on="student_id", how="left")

    for c in (
        "quiz_score_avg",
        "lightbulb_rate",
        "resolve_rate",
        "total_interactions",
    ):
        if c in df.columns:
            df[c] = df[c].fillna(0.0)

    labels_raw = (df["mastery_avg"] >= 0.65).astype(int)
    if labels_raw.nunique() < 2:
        med = float(df["mastery_avg"].median())
        labels = (df["mastery_avg"] >= med).astype(int)
        if labels.nunique() < 2:
            labels = pd.Series(0, index=df.index, dtype=int)

    else:
        labels = labels_raw

    feature_cols = [
        "quiz_score_avg",
        "mastery_avg",
        "mastery_min",
        "evidence_avg",
        "lightbulb_rate",
        "resolve_rate",
        "total_interactions",
    ]
    X = df[feature_cols].fillna(0.0).astype(np.float64)
    X.insert(0, "student_id", df["student_id"].values)

    ds = Dataset(features=X, labels=labels.reset_index(drop=True))
    return filter_dataset_by_students(
        ds,
        exclude_student_ids=exclude_student_ids,
        include_only_student_ids=include_only_student_ids,
    )
