"""ItemBank carrying calibrated 2PL (a, b) and optional distractor metadata.

The bank is built by joining:

    1. PR 5's `item_params` (per-item `a`, `b` from `fit_2pl`)
    2. PR 4's ASSISTments responses, which carry the `skill_id` that
       becomes each item's `concept_id`
    3. (optional) PR 4's Eedi frames — if an Eedi item shares a QuestionId
       with an ASSISTments problem_id, its distractor→misconception map is
       attached to the item. v1 stores this metadata but does not use it
       in response generation (spec: "v1 response model ignores
       `misconception_id`"); v2 will.

    4. (optional) A **verified crosswalk** ``assist_to_eedi_verified: dict[int, int]``
       mapping each ASSISTments ``problem_id``/``item_id`` to a **Eedi**
       ``QuestionId`` (via human or semantic + QC). When
       ``only_items_in_verified_map`` is True, only rows present in that
       map are kept, and distractor tags are taken from
       ``eedi_by_question[eedi_question_id]``, not from identity
       ``problem_id == QuestionId`` (rare in practice).

If no Eedi overlap exists, items get an empty `distractors` tuple.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Distractor:
    """One wrong-answer option with an optional misconception id."""

    option_text: str
    misconception_id: Optional[int] = None


@dataclass(frozen=True)
class Item:
    """Calibrated item entry."""

    item_id: int
    concept_id: int
    a: float
    b: float
    distractors: tuple[Distractor, ...] = field(default_factory=tuple)


class ItemBank:
    """In-memory catalogue of calibrated items, indexed by id + concept."""

    def __init__(self, items: Iterable[Item]) -> None:
        self._by_id: dict[int, Item] = {}
        self._by_concept: dict[int, list[int]] = {}
        for item in items:
            if item.item_id in self._by_id:
                raise ValueError(f"duplicate item_id {item.item_id}")
            self._by_id[item.item_id] = item
            self._by_concept.setdefault(item.concept_id, []).append(item.item_id)
        # Sort the per-concept lists so iteration is deterministic.
        for concept_id in self._by_concept:
            self._by_concept[concept_id].sort()

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._by_id

    def items(self) -> list[Item]:
        return [self._by_id[i] for i in sorted(self._by_id)]

    def get(self, item_id: int) -> Item:
        if item_id not in self._by_id:
            raise KeyError(f"unknown item_id {item_id}")
        return self._by_id[item_id]

    def concepts(self) -> list[int]:
        return sorted(self._by_concept)

    def items_for_concept(self, concept_id: int) -> list[Item]:
        return [self._by_id[i] for i in self._by_concept.get(concept_id, [])]


def _concept_lookup(responses_df: pd.DataFrame) -> dict[int, int]:
    """Pick the modal skill_id per problem_id, ignoring untagged rows."""
    needed = {"problem_id", "skill_id"}
    missing = needed - set(responses_df.columns)
    if missing:
        raise KeyError(f"ItemBank requires {needed} on responses; missing {missing}")
    df = responses_df[responses_df["skill_id"] != -1]
    if df.empty:
        return {}
    modes = (
        df.groupby(["problem_id", "skill_id"])
        .size()
        .reset_index(name="n")
        .sort_values(["problem_id", "n", "skill_id"], ascending=[True, False, True])
        .drop_duplicates("problem_id", keep="first")
    )
    return dict(zip(modes["problem_id"].astype(int), modes["skill_id"].astype(int)))


def _eedi_distractor_lookup(eedi_frames) -> dict[int, tuple[Distractor, ...]]:
    """Return {QuestionId: tuple(Distractor, ...)} from an `EediFrames`."""
    if eedi_frames is None:
        return {}
    options = eedi_frames.answer_options_df
    distractor_map = eedi_frames.distractor_misconception_map_df
    if options is None or options.empty:
        return {}

    # Only non-correct options count as distractors.
    wrong = options[~options["IsCorrect"]].copy()
    # Attach misconception id via the Question×Option join, if present.
    misc_by_qo: dict[tuple[int, str], Optional[int]] = {}
    if distractor_map is not None and not distractor_map.empty:
        for _, row in distractor_map.iterrows():
            key = (int(row["QuestionId"]), str(row["Option"]))
            mid = row["MisconceptionId"]
            misc_by_qo[key] = int(mid) if pd.notna(mid) else None

    out: dict[int, list[Distractor]] = {}
    for _, row in wrong.iterrows():
        qid = int(row["QuestionId"])
        option = str(row["Option"])
        if "OptionText" in wrong.columns and pd.notna(row.get("OptionText")):
            text = str(row["OptionText"])
        elif "Text" in wrong.columns and pd.notna(row.get("Text")):
            text = str(row["Text"])
        else:
            text = ""
        misc = misc_by_qo.get((qid, option))
        out.setdefault(qid, []).append(
            Distractor(option_text=text, misconception_id=misc)
        )
    return {qid: tuple(ds) for qid, ds in out.items()}


def _remap_verified_assist_ids_to_item_ids(
    assist_to_eedi_verified: dict[int, int],
    responses_df: pd.DataFrame,
    item_params: pd.DataFrame,
) -> dict[int, int]:
    """Translate crosswalk ASSISTments ids onto calibrated item_id/problem_id space.

    The verified crosswalk may key rows by identifiers like `problem_log_id`
    instead of calibrated `problem_id` (`item_id` in Gate A params). This tries
    a direct join first; if weak, it derives a modal mapping from response id
    columns to `problem_id` and remaps.
    """
    if not assist_to_eedi_verified:
        return {}
    item_ids = set(pd.to_numeric(item_params["item_id"], errors="coerce").dropna().astype(int))
    direct_overlap = sum(1 for k in assist_to_eedi_verified if int(k) in item_ids)
    best_map = dict(assist_to_eedi_verified)
    best_overlap = direct_overlap

    if "problem_id" not in responses_df.columns:
        return best_map

    candidates = (
        "problem_log_id",
        "assistments_item_id",
        "item_id",
        "problem",
    )
    for c in candidates:
        if c not in responses_df.columns:
            continue
        bridge = responses_df[[c, "problem_id"]].copy()
        bridge[c] = pd.to_numeric(bridge[c], errors="coerce")
        bridge["problem_id"] = pd.to_numeric(bridge["problem_id"], errors="coerce")
        bridge = bridge.dropna(subset=[c, "problem_id"])
        if bridge.empty:
            continue
        bridge[c] = bridge[c].astype(int)
        bridge["problem_id"] = bridge["problem_id"].astype(int)
        modal = (
            bridge.groupby([c, "problem_id"])
            .size()
            .reset_index(name="n")
            .sort_values([c, "n", "problem_id"], ascending=[True, False, True])
            .drop_duplicates(c, keep="first")
        )
        lookup = dict(zip(modal[c].astype(int), modal["problem_id"].astype(int)))
        remapped: dict[int, int] = {}
        for aid, eedi_q in assist_to_eedi_verified.items():
            pid = lookup.get(int(aid))
            if pid is None:
                continue
            if pid not in remapped:
                remapped[pid] = int(eedi_q)
        overlap = sum(1 for k in remapped if k in item_ids)
        if overlap > best_overlap:
            best_overlap = overlap
            best_map = remapped

    return best_map


def load_verified_assistments_eedi_map(path: str | Path) -> dict[int, int]:
    """Load ``data/processed/assistments_eedi_verified_crosswalk.csv``.

    Required columns (case-insensitive; aliases allowed):

    - **assistments item id** — one of: ``assistments_problem_id``,
      ``assistments_item_id``, ``problem_id``, ``item_id``
    - **Eedi id** — one of: ``eedi_question_id``, ``QuestionId``,
      ``question_id``
    - **verified** (optional) — if present, only rows with truthy
      values are kept (``1``, ``true``, ``yes``).

    Duplicate assist ids: first row wins in file order. Empty path or
    missing file raises ``FileNotFoundError``.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"verified crosswalk not found: {p}")

    df = pd.read_csv(p, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    col_lower = {c.lower(): c for c in df.columns}
    a_col = next(
        (
            col_lower[k]
            for k in (
                "assistments_problem_id",
                "assistments_item_id",
                "problem_id",
                "item_id",
            )
            if k in col_lower
        ),
        None,
    )
    e_col = next(
        (
            col_lower[k]
            for k in (
                "eedi_question_id",
                "questionid",
                "question_id",
            )
            if k in col_lower
        ),
        None,
    )
    if a_col is None or e_col is None:
        raise KeyError(
            f"Crosswalk {p} must include an ASSISTments id and Eedi QuestionId "
            f"column. Got: {list(df.columns)}"
        )
    v_col = col_lower.get("verified")
    if v_col is not None:
        def _ok_verified(x: object) -> bool:
            if x is None:
                return False
            if isinstance(x, (bool, np.bool_)):
                return bool(x)
            if isinstance(x, (int, float, np.integer, np.floating)) and not isinstance(
                x, (bool, np.bool_)
            ):
                if isinstance(x, float) and (pd.isna(x) or np.isnan(x)):
                    return False
                try:
                    return int(x) == 1
                except (ValueError, OverflowError):
                    return False
            if isinstance(x, str) and not x.strip():
                return False
            s = str(x).strip().lower()
            if s in ("0", "false", "no", "f", "n", ""):
                return False
            if s in ("1", "true", "yes", "t", "y"):
                return True
            try:
                return int(float(s)) == 1
            except (TypeError, ValueError):
                return False

        df = df[df[v_col].map(_ok_verified)].copy()
    out: dict[int, int] = {}
    for _, row in df.iterrows():
        try:
            aid = int(float(row[a_col]))
            eid = int(float(row[e_col]))
        except (TypeError, ValueError):
            continue
        if aid not in out:
            out[aid] = eid
    return out


def build_item_bank(
    item_params: pd.DataFrame,
    responses_df: pd.DataFrame,
    eedi_frames=None,
    assist_to_eedi_verified: dict[int, int] | None = None,
    only_items_in_verified_map: bool = False,
) -> ItemBank:
    """Assemble an `ItemBank` from calibrated params + responses (+ optional Eedi).

    `item_params` must have columns ``item_id, a, b`` (the output of
    `fit_2pl.write_item_params`). Items without a `concept_id` match
    in `responses_df` are skipped with a warning — they can't be placed
    on the concept graph so they're not usable in the loop.

    If ``assist_to_eedi_verified`` is not None, distractor/misconception
    metadata is taken from
    ``eedi_by_question[ assist_to_eedi_verified[item_id] ]`` when
    present. If ``only_items_in_verified_map`` is True, any calibrated
    item not listed in the map is omitted from the bank (ablation
    “Eedi-anchored” subset).
    """
    needed = {"item_id", "a", "b"}
    missing = needed - set(item_params.columns)
    if missing:
        raise KeyError(f"item_params missing {missing}")

    concept_by_item = _concept_lookup(responses_df)
    eedi_by_question = _eedi_distractor_lookup(eedi_frames)
    verified_map = assist_to_eedi_verified
    if assist_to_eedi_verified is not None:
        verified_map = _remap_verified_assist_ids_to_item_ids(
            assist_to_eedi_verified=assist_to_eedi_verified,
            responses_df=responses_df,
            item_params=item_params,
        )
    if assist_to_eedi_verified is not None and only_items_in_verified_map:
        assist_ok = set(verified_map or {})

    items: list[Item] = []
    for row in item_params.itertuples(index=False):
        item_id = int(row.item_id)
        if assist_to_eedi_verified is not None and only_items_in_verified_map:
            if item_id not in assist_ok:
                continue
        concept_id = concept_by_item.get(item_id)
        if concept_id is None:
            continue
        if assist_to_eedi_verified is not None:
            eedi_q: Optional[int] = None if verified_map is None else verified_map.get(item_id)
            if eedi_q is not None:
                distractors = eedi_by_question.get(int(eedi_q), ())
            else:
                if only_items_in_verified_map:
                    continue
                distractors = eedi_by_question.get(item_id, ())
        else:
            distractors = eedi_by_question.get(item_id, ())
        items.append(
            Item(
                item_id=item_id,
                concept_id=int(concept_id),
                a=float(row.a),
                b=float(row.b),
                distractors=distractors,
            )
        )
    return ItemBank(items)
