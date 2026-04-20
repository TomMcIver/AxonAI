"""Leakage check for the 2PL train/heldout split.

`fit_2pl._split_heldout` partitions source rows per item. True leakage is
the same *source row* appearing on both sides of the split. Equal-key
tuples `(user_id, problem_id, correct)` are *not* leakage — ASSISTments
legitimately has multiple attempts by the same user on the same item
with the same correctness, and IRT treats each as an independent trial.

Row identity is, in order of preference:

    1. `problem_log_id`  (ASSISTments canonical row id).
    2. The DataFrame's positional index (set by the loader from pandas
       read_csv; kept intact through `_split_heldout`).

Shared `user_id`s and `problem_id`s across the split are *expected* and
necessary — IRT fits theta per user and (a, b) per item by definition.

Usage:
    report = run(train_df, test_df)
    print(report.summary_markdown())
    assert report.passed

Acceptance rule: `duplicate_rows == 0`. Non-zero indicates a bug in the
loader or `_split_heldout`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

_ROW_ID_CANDIDATES = ("problem_log_id",)


def _row_identity(df: pd.DataFrame) -> pd.Series:
    """Return a Series of row identities, preferring a shipped id column."""
    for col in _ROW_ID_CANDIDATES:
        if col in df.columns:
            return df[col]
    return pd.Series(df.index, index=df.index, name="__row_index__")


@dataclass(frozen=True)
class LeakageReport:
    n_train: int
    n_heldout: int
    duplicate_rows: int
    shared_items: int
    shared_users: int
    unique_train_items: int
    unique_heldout_items: int
    unique_train_users: int
    unique_heldout_users: int
    identity_column: str

    @property
    def passed(self) -> bool:
        return self.duplicate_rows == 0

    def summary_markdown(self) -> str:
        lines = [
            "### Leakage check",
            "",
            f"- Row identity: `{self.identity_column}`",
            f"- Train rows: {self.n_train:,}",
            f"- Heldout rows: {self.n_heldout:,}",
            f"- Source rows appearing on both sides: **{self.duplicate_rows:,}**",
            f"- Items appearing in both splits: {self.shared_items:,} "
            f"(train: {self.unique_train_items:,}, heldout: {self.unique_heldout_items:,})",
            f"- Users appearing in both splits: {self.shared_users:,} "
            f"(train: {self.unique_train_users:,}, heldout: {self.unique_heldout_users:,})",
            f"- Status: {'PASS' if self.passed else 'FAIL — investigate'}",
            "",
            "Note: per-item and per-user overlap is expected and necessary "
            "for IRT (theta is fit per user across their training rows "
            "and evaluated on heldout rows of the same items). Only "
            "`source rows appearing on both sides > 0` is leakage.",
        ]
        return "\n".join(lines) + "\n"


def run(train_df: pd.DataFrame, heldout_df: pd.DataFrame) -> LeakageReport:
    """Compare train vs heldout slices for source-row duplication."""
    for name, df in ("train", train_df), ("heldout", heldout_df):
        for col in ("user_id", "problem_id", "correct"):
            if col not in df.columns:
                raise KeyError(f"{name} frame missing required column {col!r}")

    train_id = _row_identity(train_df)
    held_id = _row_identity(heldout_df)
    id_col = train_id.name if train_id.name not in (None, "__row_index__") else "index"

    duplicate_rows = int(pd.Index(train_id).intersection(pd.Index(held_id)).size)

    train_items = set(train_df["problem_id"].unique())
    heldout_items = set(heldout_df["problem_id"].unique())
    train_users = set(train_df["user_id"].unique())
    heldout_users = set(heldout_df["user_id"].unique())

    return LeakageReport(
        n_train=len(train_df),
        n_heldout=len(heldout_df),
        duplicate_rows=duplicate_rows,
        shared_items=len(train_items & heldout_items),
        shared_users=len(train_users & heldout_users),
        unique_train_items=len(train_items),
        unique_heldout_items=len(heldout_items),
        unique_train_users=len(train_users),
        unique_heldout_users=len(heldout_users),
        identity_column=str(id_col),
    )
