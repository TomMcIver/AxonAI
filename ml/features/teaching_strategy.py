"""Teaching strategy success feature set (pedagogical_memory rows)."""

from __future__ import annotations

from typing import AbstractSet, Optional

import numpy as np
import pandas as pd

from db import get_connection

from . import Dataset
from .student_filters import filter_dataset_by_students


def build_strategy_dataset(
    *,
    exclude_student_ids: Optional[AbstractSet[int]] = None,
    include_only_student_ids: Optional[AbstractSet[int]] = None,
) -> Dataset:
    """
    Features: one-hot teaching_approach, concept_type, dominant_learning_style;
    mastery for concepts of that type; frustration_threshold.
    Label: 1 if success_rate >= 0.5.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT pm.id AS pm_id,
                   pm.student_id,
                   pm.teaching_approach,
                   pm.concept_type,
                   pm.success_rate,
                   COALESCE(slp.frustration_threshold, 0.5) AS frustration_threshold,
                   COALESCE(slp.dominant_learning_style, 'unknown') AS dominant_learning_style,
                   (
                       SELECT AVG(cms.mastery_score)
                       FROM concept_mastery_states cms
                       INNER JOIN concepts c ON c.id = cms.concept_id
                       WHERE cms.student_id = pm.student_id
                         AND pm.concept_type IS NOT NULL
                         AND c.concept_type = pm.concept_type
                   ) AS mastery_for_concept_type
            FROM pedagogical_memory pm
            LEFT JOIN student_learning_profiles slp
              ON slp.student_id = pm.student_id
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        empty = pd.DataFrame()
        return Dataset(features=empty, labels=pd.Series(dtype=int))

    df["mastery_for_concept_type"] = df["mastery_for_concept_type"].fillna(0.0)
    labels = (df["success_rate"].fillna(0.0) >= 0.5).astype(int)

    cat_cols = ["teaching_approach", "concept_type", "dominant_learning_style"]
    dummies = pd.get_dummies(
        df[cat_cols].fillna("unknown"),
        columns=cat_cols,
        prefix=cat_cols,
        dtype=float,
    )

    base = df[
        ["student_id", "pm_id", "frustration_threshold", "mastery_for_concept_type"]
    ].copy()
    base["_meta_teaching_approach"] = df["teaching_approach"].fillna("")
    base["_meta_concept_type"] = df["concept_type"].fillna("")
    base["frustration_threshold"] = base["frustration_threshold"].astype(np.float64)
    base["mastery_for_concept_type"] = base["mastery_for_concept_type"].astype(np.float64)

    X = pd.concat([base, dummies], axis=1)
    ds = Dataset(features=X, labels=labels.reset_index(drop=True))
    return filter_dataset_by_students(
        ds,
        exclude_student_ids=exclude_student_ids,
        include_only_student_ids=include_only_student_ids,
    )
