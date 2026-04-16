"""Engagement regression feature set (student-level)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AbstractSet, Optional

import numpy as np
import pandas as pd

from db import get_connection

from . import Dataset
from .student_filters import filter_dataset_by_students


def _engagement_slope_last_n(
    sessions: pd.DataFrame, n: int = 10
) -> pd.Series:
    """Per student: linear slope of session_engagement_score over last n sessions (chronological)."""
    slopes = {}
    for sid, g in sessions.groupby("student_id"):
        g2 = g.sort_values("started_at").tail(n)
        y = g2["session_engagement_score"].astype(float)
        if len(g2) < 2 or y.notna().sum() < 2:
            slopes[sid] = 0.0
            continue
        y = y.fillna(y.mean())
        x = np.arange(len(g2), dtype=float)
        coef = np.polyfit(x, y.values, 1)
        slopes[sid] = float(coef[0])
    return pd.Series(slopes, name="engagement_slope")


def build_engagement_dataset(
    *,
    exclude_student_ids: Optional[AbstractSet[int]] = None,
    include_only_student_ids: Optional[AbstractSet[int]] = None,
) -> Dataset:
    """
    Features: slope of session_engagement over last 10 sessions, avg response time,
    avg word count, lightbulb rate, days_since_last_interaction.
    Label: overall_engagement_score (continuous).
    """
    conn = get_connection()
    try:
        prof = pd.read_sql(
            """
            SELECT student_id,
                   COALESCE(overall_engagement_score, 0) AS overall_engagement_score,
                   last_interaction_at,
                   COALESCE(average_response_time_seconds, 0) AS avg_response_time_seconds
            FROM student_learning_profiles
            """,
            conn,
        )
        sessions = pd.read_sql(
            """
            SELECT student_id, started_at, session_engagement_score
            FROM conversations
            WHERE session_engagement_score IS NOT NULL
            ORDER BY student_id, started_at
            """,
            conn,
        )
        msg = pd.read_sql(
            """
            SELECT student_id,
                   AVG(word_count::float) AS word_count_avg,
                   AVG(CASE WHEN is_lightbulb_moment THEN 1.0 ELSE 0.0 END)
                       AS lightbulb_rate
            FROM messages
            GROUP BY student_id
            """,
            conn,
        )
        conv_lb = pd.read_sql(
            """
            SELECT student_id,
                   AVG(CASE WHEN lightbulb_moment_detected THEN 1.0 ELSE 0.0 END)
                       AS conv_lightbulb_rate
            FROM conversations
            GROUP BY student_id
            """,
            conn,
        )
    finally:
        conn.close()

    now = datetime.now(timezone.utc)
    if not sessions.empty and sessions["started_at"].dt.tz is None:
        sessions = sessions.copy()
        sessions["started_at"] = pd.to_datetime(sessions["started_at"], utc=True)

    slope_series = (
        _engagement_slope_last_n(sessions, 10)
        if not sessions.empty
        else pd.Series(dtype=float)
    )

    df = prof.merge(
        slope_series.rename("engagement_slope"),
        left_on="student_id",
        right_index=True,
        how="left",
    )
    df = df.merge(msg, on="student_id", how="left")
    df = df.merge(conv_lb, on="student_id", how="left")

    df["engagement_slope"] = df["engagement_slope"].fillna(0.0)
    df["word_count_avg"] = df["word_count_avg"].fillna(0.0)
    # Prefer message-level lightbulb rate; fall back to conversation-level
    df["lightbulb_rate"] = df["lightbulb_rate"].fillna(df["conv_lightbulb_rate"]).fillna(
        0.0
    )
    df.drop(columns=["conv_lightbulb_rate"], inplace=True, errors="ignore")

    def _days_since(ts) -> float:
        if ts is None or (isinstance(ts, float) and np.isnan(ts)):
            return 365.0
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize(timezone.utc)
        return max(0.0, (now - t.to_pydatetime()).total_seconds() / 86400.0)

    df["days_since_last_interaction"] = df["last_interaction_at"].apply(_days_since)

    labels = df["overall_engagement_score"].astype(float).fillna(0.0)

    feature_cols = [
        "engagement_slope",
        "avg_response_time_seconds",
        "word_count_avg",
        "lightbulb_rate",
        "days_since_last_interaction",
    ]
    X = df[feature_cols].fillna(0.0).astype(np.float64)
    X.insert(0, "student_id", df["student_id"].values)

    ds = Dataset(features=X, labels=labels.reset_index(drop=True))
    return filter_dataset_by_students(
        ds,
        exclude_student_ids=exclude_student_ids,
        include_only_student_ids=include_only_student_ids,
    )
