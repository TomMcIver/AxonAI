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

If no Eedi overlap exists, items get an empty `distractors` tuple.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

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


def build_item_bank(
    item_params: pd.DataFrame,
    responses_df: pd.DataFrame,
    eedi_frames=None,
) -> ItemBank:
    """Assemble an `ItemBank` from calibrated params + responses (+ optional Eedi).

    `item_params` must have columns ``item_id, a, b`` (the output of
    `fit_2pl.write_item_params`). Items without a `concept_id` match
    in `responses_df` are skipped with a warning — they can't be placed
    on the concept graph so they're not usable in the loop.
    """
    needed = {"item_id", "a", "b"}
    missing = needed - set(item_params.columns)
    if missing:
        raise KeyError(f"item_params missing {missing}")

    concept_by_item = _concept_lookup(responses_df)
    eedi_by_question = _eedi_distractor_lookup(eedi_frames)

    items: list[Item] = []
    for row in item_params.itertuples(index=False):
        item_id = int(row.item_id)
        concept_id = concept_by_item.get(item_id)
        if concept_id is None:
            continue
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
