"""Unit tests for ml.simulator.calibration.leakage_check."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.simulator.calibration.fit_2pl import (
    HELDOUT_FRACTION,
    _split_heldout,
)
from ml.simulator.calibration.leakage_check import run


def _fake_responses(n_users: int, n_items: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for u in range(n_users):
        # Each user answers a random 60% of items, twice on half of those
        # (so repeat rows exist — the common pathology that fooled the
        # earlier value-triple leakage check).
        items = rng.choice(n_items, size=int(n_items * 0.6), replace=False)
        for it in items:
            rows.append((u, int(it), bool(rng.random() < 0.5)))
            if rng.random() < 0.5:
                rows.append((u, int(it), bool(rng.random() < 0.5)))
    df = pd.DataFrame(rows, columns=["user_id", "problem_id", "correct"])
    # Keep only items with >=5 responses to ensure the split has headroom.
    kept = df.groupby("problem_id").size()
    df = df[df["problem_id"].isin(kept[kept >= 5].index)].reset_index(drop=True)
    return df


def test_leakage_passes_on_clean_split():
    df = _fake_responses(n_users=80, n_items=20, seed=1)
    rng = np.random.default_rng(42)
    train, held = _split_heldout(df, rng, HELDOUT_FRACTION)
    report = run(train, held)
    assert report.passed
    assert report.duplicate_rows == 0


def test_leakage_fails_when_row_appears_on_both_sides():
    df = _fake_responses(n_users=60, n_items=15, seed=7)
    rng = np.random.default_rng(42)
    train, held = _split_heldout(df, rng, HELDOUT_FRACTION)
    # Inject a leak: copy one train row into heldout.
    held_leaked = pd.concat([held, train.iloc[[0]]])
    report = run(train, held_leaked)
    assert not report.passed
    assert report.duplicate_rows == 1


def test_leakage_ignores_value_triple_repeats():
    """Two source rows with identical (user, item, correct) are not leakage.

    ASSISTments has genuine multi-attempt rows; the leakage check must
    use row identity (preserved through the split), not value hashing.
    """
    # Hand-built frame with repeat (user, item, correct) rows.
    df = pd.DataFrame(
        [
            (1, 10, True),
            (1, 10, True),   # genuine repeat attempt
            (1, 10, True),   # genuine repeat attempt
            (1, 10, True),
            (1, 10, True),
            (2, 10, False),
            (2, 10, False),
            (2, 10, False),
            (2, 10, False),
            (2, 10, False),
        ],
        columns=["user_id", "problem_id", "correct"],
    )
    # Manual split: first five rows train, last five heldout.
    train = df.iloc[:5]
    held = df.iloc[5:]
    report = run(train, held)
    assert report.passed, report.summary_markdown()


def test_leakage_requires_core_columns():
    df = pd.DataFrame({"user_id": [1], "problem_id": [1]})
    with pytest.raises(KeyError):
        run(df, df)
