"""Tests for the ItemBank assembly."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from ml.simulator.data.item_bank import (
    Distractor,
    Item,
    ItemBank,
    build_item_bank,
    load_verified_assistments_eedi_map,
)


@pytest.fixture
def item_params() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"item_id": 10, "a": 1.2, "b": -0.5},
            {"item_id": 11, "a": 0.9, "b": 0.3},
            {"item_id": 12, "a": 1.5, "b": 1.1},
            {"item_id": 99, "a": 1.0, "b": 0.0},  # no concept in responses → dropped
        ]
    )


@pytest.fixture
def responses() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"user_id": 1, "problem_id": 10, "problem_log_id": 10010, "skill_id": 7},
            {"user_id": 2, "problem_id": 10, "problem_log_id": 10010, "skill_id": 7},
            {"user_id": 3, "problem_id": 10, "problem_log_id": 10010, "skill_id": 8},  # minority
            {"user_id": 1, "problem_id": 11, "problem_log_id": 10011, "skill_id": 8},
            {"user_id": 1, "problem_id": 12, "problem_log_id": 10012, "skill_id": 9},
            {"user_id": 2, "problem_id": 12, "problem_log_id": 10012, "skill_id": 9},
            # item 99 has only untagged rows — should not resolve to a concept
            {"user_id": 1, "problem_id": 99, "problem_log_id": 10099, "skill_id": -1},
        ]
    )


@pytest.fixture
def eedi_frames():
    # Eedi questions 10 and 2000: crosswalk can map assist 10 -> 2000.
    options = pd.DataFrame(
        [
            {"QuestionId": 10, "Option": "A", "OptionText": "right", "IsCorrect": True},
            {"QuestionId": 10, "Option": "B", "OptionText": "wrongB", "IsCorrect": False},
            {"QuestionId": 10, "Option": "C", "OptionText": "wrongC", "IsCorrect": False},
            {"QuestionId": 10, "Option": "D", "OptionText": "wrongD", "IsCorrect": False},
            {"QuestionId": 2000, "Option": "A", "OptionText": "r2", "IsCorrect": True},
            {"QuestionId": 2000, "Option": "B", "OptionText": "b2000", "IsCorrect": False},
            {"QuestionId": 2000, "Option": "C", "OptionText": "c2000", "IsCorrect": False},
            {"QuestionId": 2000, "Option": "D", "OptionText": "d2000", "IsCorrect": False},
        ]
    )
    distractor_map = pd.DataFrame(
        [
            {"QuestionId": 10, "Option": "B", "MisconceptionId": 1672},
            {"QuestionId": 10, "Option": "D", "MisconceptionId": 2142},
            {"QuestionId": 2000, "Option": "B", "MisconceptionId": 99},
        ]
    )
    return SimpleNamespace(
        questions_df=pd.DataFrame(),
        answer_options_df=options,
        distractor_misconception_map_df=distractor_map,
        misconception_catalogue_df=pd.DataFrame(),
    )


class TestItemBank:
    def test_indexes_by_id_and_concept(self) -> None:
        bank = ItemBank([
            Item(item_id=1, concept_id=7, a=1.0, b=0.0),
            Item(item_id=2, concept_id=7, a=1.1, b=0.2),
            Item(item_id=3, concept_id=8, a=0.8, b=-0.3),
        ])
        assert len(bank) == 3
        assert 1 in bank
        assert 4 not in bank
        assert bank.concepts() == [7, 8]
        assert [i.item_id for i in bank.items_for_concept(7)] == [1, 2]
        assert bank.get(2).a == 1.1

    def test_duplicate_item_id_raises(self) -> None:
        with pytest.raises(ValueError):
            ItemBank([
                Item(item_id=1, concept_id=7, a=1.0, b=0.0),
                Item(item_id=1, concept_id=8, a=0.5, b=0.5),
            ])

    def test_get_unknown_id_raises(self) -> None:
        bank = ItemBank([Item(item_id=1, concept_id=7, a=1.0, b=0.0)])
        with pytest.raises(KeyError):
            bank.get(99)


class TestBuildItemBank:
    def test_drops_items_without_concept(self, item_params, responses) -> None:
        bank = build_item_bank(item_params, responses)
        item_ids = [i.item_id for i in bank.items()]
        assert 99 not in item_ids
        assert item_ids == [10, 11, 12]

    def test_modal_concept_assignment(self, item_params, responses) -> None:
        # Item 10 has 2 users with skill=7 and 1 with skill=8 → modal is 7.
        bank = build_item_bank(item_params, responses)
        assert bank.get(10).concept_id == 7

    def test_params_copied_through(self, item_params, responses) -> None:
        bank = build_item_bank(item_params, responses)
        entry = bank.get(11)
        assert entry.a == pytest.approx(0.9)
        assert entry.b == pytest.approx(0.3)
        assert entry.distractors == ()  # no Eedi passed

    def test_eedi_distractors_attached(self, item_params, responses, eedi_frames) -> None:
        bank = build_item_bank(item_params, responses, eedi_frames=eedi_frames)
        entry = bank.get(10)
        assert len(entry.distractors) == 3
        # Option B should carry misconception 1672, C should be None, D should be 2142.
        by_text = {d.option_text: d for d in entry.distractors}
        assert by_text["wrongB"].misconception_id == 1672
        assert by_text["wrongC"].misconception_id is None
        assert by_text["wrongD"].misconception_id == 2142
        # Correct option must not appear.
        assert all(d.option_text != "right" for d in entry.distractors)

    def test_item_without_eedi_match_has_empty_distractors(
        self, item_params, responses, eedi_frames
    ) -> None:
        bank = build_item_bank(item_params, responses, eedi_frames=eedi_frames)
        assert bank.get(11).distractors == ()

    def test_missing_param_columns_raise(self, responses) -> None:
        bad = pd.DataFrame({"item_id": [1], "a": [1.0]})
        with pytest.raises(KeyError):
            build_item_bank(bad, responses)

    def test_missing_response_columns_raise(self, item_params) -> None:
        bad = pd.DataFrame({"user_id": [0]})
        with pytest.raises(KeyError):
            build_item_bank(item_params, bad)

    def test_verified_crosswalk_maps_different_eedi_id(
        self, item_params, responses, eedi_frames
    ) -> None:
        """Assist 10 uses Eedi Question 2000 via map; only mapped items in bank when flagged."""
        xw = {10: 2000}
        bank = build_item_bank(
            item_params,
            responses,
            eedi_frames=eedi_frames,
            assist_to_eedi_verified=xw,
            only_items_in_verified_map=True,
        )
        assert {i.item_id for i in bank.items()} == {10}
        d0 = {d.option_text: d for d in bank.get(10).distractors}
        assert d0["b2000"].misconception_id == 99
        assert len(d0) == 3

    def test_load_verified_crosswalk_filters_and_aliases(self, tmp_path) -> None:
        f = tmp_path / "x.csv"
        f.write_text(
            "problem_id,eedi_question_id,verified\n"
            "10,100,true\n"
            "10,200,false\n"  # duplicate assist id: first wins
            "11,101,no\n"
            "12,102,yes\n",
            encoding="utf-8",
        )
        m = load_verified_assistments_eedi_map(f)
        assert m == {10: 100, 12: 102}

    def test_verified_crosswalk_problem_log_id_remaps_to_problem_id(
        self, item_params, responses, eedi_frames
    ) -> None:
        # Crosswalk ids are problem_log_id-like, not calibrated item_id/problem_id.
        xw = {10010: 2000}
        bank = build_item_bank(
            item_params,
            responses,
            eedi_frames=eedi_frames,
            assist_to_eedi_verified=xw,
            only_items_in_verified_map=True,
        )
        assert {i.item_id for i in bank.items()} == {10}
        by_text = {d.option_text: d for d in bank.get(10).distractors}
        assert by_text["b2000"].misconception_id == 99
