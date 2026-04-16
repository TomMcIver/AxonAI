"""Filter feature frames and labels by student_id for train vs holdout."""

from __future__ import annotations

from typing import AbstractSet, Optional

import pandas as pd

from . import Dataset


def filter_dataset_by_students(
    ds: Dataset,
    *,
    exclude_student_ids: Optional[AbstractSet[int]] = None,
    include_only_student_ids: Optional[AbstractSet[int]] = None,
) -> Dataset:
    """
    If `include_only_student_ids` is set, keep only those students.
    Else if `exclude_student_ids` is set, drop those students.
    """
    df = ds.features
    lab = ds.labels.reset_index(drop=True)
    if df.empty:
        return ds

    if include_only_student_ids is not None:
        mask = df["student_id"].isin(include_only_student_ids)
    elif exclude_student_ids:
        mask = ~df["student_id"].isin(exclude_student_ids)
    else:
        return Dataset(features=df.reset_index(drop=True), labels=lab)

    m = mask.values
    f2 = df.loc[mask].reset_index(drop=True)
    lab2 = lab[m].reset_index(drop=True)
    return Dataset(features=f2, labels=lab2)
