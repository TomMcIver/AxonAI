"""
Students excluded from *training* so models can be applied to them as holdout / demo.

Keep in sync with frontend `frontend/src/constants/demoStudents.js` (DEMO_STUDENT_IDS).
Also honors RDS `students.is_demo_student` and optional env `AXONAI_ML_EXCLUDE_STUDENT_IDS`.
"""

from __future__ import annotations

import os
from typing import FrozenSet, Set

from db import get_connection

# Must match frontend/src/constants/demoStudents.js — single source for dashboard demos.
FRONTEND_DEMO_STUDENT_IDS: FrozenSet[int] = frozenset(
    [
        1,
        547,
        548,
        549,
        550,
        551,
        552,
        553,
        554,
        555,
        556,
        557,
        558,
        559,
        560,
        561,
        562,
        563,
        564,
        565,
        566,
        567,
        568,
        569,
        570,
        571,
    ]
)


def _parse_env_extra_ids() -> Set[int]:
    raw = os.environ.get("AXONAI_ML_EXCLUDE_STUDENT_IDS", "").strip()
    if not raw:
        return set()
    out: Set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return out


def _query_demo_flag_student_ids(conn) -> Set[int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM students
            WHERE is_demo_student IS TRUE
            """
        )
        return {row[0] for row in cur.fetchall()}


def get_training_excluded_student_ids(conn=None) -> FrozenSet[int]:
    """
    Union of:
    - `students.is_demo_student = TRUE`
    - `FRONTEND_DEMO_STUDENT_IDS` (matches teacher UI cohort)
    - `AXONAI_ML_EXCLUDE_STUDENT_IDS` (comma-separated)
    """
    close = False
    if conn is None:
        conn = get_connection()
        close = True
    try:
        db_ids = _query_demo_flag_student_ids(conn)
    finally:
        if close:
            conn.close()
    merged: Set[int] = set(db_ids) | set(FRONTEND_DEMO_STUDENT_IDS) | _parse_env_extra_ids()
    return frozenset(merged)
