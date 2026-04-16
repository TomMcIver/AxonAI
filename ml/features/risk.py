"""At-risk classification feature set (student-level)."""

from __future__ import annotations

from typing import AbstractSet, Optional

import numpy as np
import pandas as pd

from db import get_connection

from . import Dataset
from .student_filters import filter_dataset_by_students


def build_risk_dataset(
    *,
    exclude_student_ids: Optional[AbstractSet[int]] = None,
    include_only_student_ids: Optional[AbstractSet[int]] = None,
) -> Dataset:
    """
    Features: overall_risk_score, overall_engagement_score, avg quiz %,
    active flag count, message frustration rate, conversation abandon rate.
    Label: 1 if overall_risk_score >= 0.4 OR (has quizzes and avg quiz < 50).
    """
    conn = get_connection()
    try:
        prof = pd.read_sql(
            """
            SELECT student_id,
                   COALESCE(overall_risk_score, 0) AS overall_risk_score,
                   COALESCE(overall_engagement_score, 0) AS overall_engagement_score
            FROM student_learning_profiles
            """,
            conn,
        )
        quizzes = pd.read_sql(
            """
            SELECT student_id,
                   AVG(score_percentage) AS quiz_score_avg,
                   COUNT(*)::int AS quiz_count
            FROM quiz_sessions
            WHERE score_percentage IS NOT NULL
            GROUP BY student_id
            """,
            conn,
        )
        flags = pd.read_sql(
            """
            SELECT student_id, COUNT(*)::int AS active_flag_count
            FROM student_concept_flags
            WHERE is_active IS TRUE
            GROUP BY student_id
            """,
            conn,
        )
        msg_rates = pd.read_sql(
            """
            SELECT m.student_id,
                   AVG(CASE WHEN m.frustration_signal THEN 1.0 ELSE 0.0 END)
                       AS frustration_rate
            FROM messages m
            GROUP BY m.student_id
            """,
            conn,
        )
        abandon = pd.read_sql(
            """
            SELECT student_id,
                   AVG(CASE WHEN outcome = 'abandoned' THEN 1.0 ELSE 0.0 END)
                       AS abandon_rate
            FROM conversations
            GROUP BY student_id
            """,
            conn,
        )
    finally:
        conn.close()

    df = prof.merge(quizzes, on="student_id", how="left")
    df = df.merge(flags, on="student_id", how="left")
    df = df.merge(msg_rates, on="student_id", how="left")
    df = df.merge(abandon, on="student_id", how="left")

    df["quiz_score_avg"] = df["quiz_score_avg"].fillna(np.nan)
    df["quiz_count"] = df["quiz_count"].fillna(0).astype(int)
    df["active_flag_count"] = df["active_flag_count"].fillna(0).astype(int)
    df["frustration_rate"] = df["frustration_rate"].fillna(0.0)
    df["abandon_rate"] = df["abandon_rate"].fillna(0.0)

    low_quiz = (df["quiz_count"] > 0) & (df["quiz_score_avg"] < 50)
    labels = ((df["overall_risk_score"] >= 0.4) | low_quiz).astype(int)

    feature_cols = [
        "overall_risk_score",
        "overall_engagement_score",
        "quiz_score_avg",
        "active_flag_count",
        "frustration_rate",
        "abandon_rate",
    ]
    X = df[feature_cols].copy()
    X["quiz_score_avg"] = X["quiz_score_avg"].fillna(0.0)
    X = X.astype(np.float64)
    X.insert(0, "student_id", df["student_id"].values)

    ds = Dataset(features=X, labels=labels.reset_index(drop=True))
    return filter_dataset_by_students(
        ds,
        exclude_student_ids=exclude_student_ids,
        include_only_student_ids=include_only_student_ids,
    )
