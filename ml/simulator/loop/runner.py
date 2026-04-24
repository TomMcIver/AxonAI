"""TermRunner — drives the Teach → Revise → Quiz loop across a term.

Each session (one per configured interval):

    1. Advance simulated time and apply forgetting.
    2. **Teach**: pick the next concept via `ConceptGraph.topological_next`
       given the student's mastery set; emit a `TeachRecord`.
    3. **Quiz**: practise `QUIZ_ITEMS_PER_SESSION` items on the
       newly-taught concept, selecting each via `select_next_item` and
       resolving it via `simulate_response`; `apply_practice` on each.
    4. **Revise**: pick concepts in the HLR "desirable difficulty" band
       and practise one item on each.
    5. Emit a `SessionEndRecord`.

The runner yields events lazily so the writer in PR 9 can stream them
to disk without holding the whole term in memory. Item Elo ratings are
kept in a runner-local dict, initialised to `INITIAL_ITEM_ELO` the first
time each item is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterator, Union

import numpy as np

from ml.simulator.data.concept_graph import ConceptGraph
from ml.simulator.data.item_bank import ItemBank
from ml.simulator.loop.explanation_style import (
    DetectorHint,
    ExplanationStyleConfig,
    select_explanation_style,
)
from ml.simulator.loop.llm_tutor import LLMTutor
from ml.simulator.loop.quiz import select_next_item, simulate_response
from ml.simulator.loop.revise import ReviseRecord, select_revision_concepts
from ml.simulator.loop.teach import TeachRecord, teach
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.psychometrics.bkt import BKTParams
from ml.simulator.student.dynamics import apply_forgetting, apply_practice
from ml.simulator.student.profile import AttemptRecord, StudentProfile

# Mastery threshold: once BKT p_known for a concept exceeds this, the
# student is considered ready for the next topological concept. Matches
# the common BKT 0.85 convention (Corbett & Anderson 1995 §5).
_MASTERY_THRESHOLD = 0.85
# Fresh-item Elo starting point.
INITIAL_ITEM_ELO = 1200.0
# Default session cadence. Spec validation run uses 10 weeks × ~7 sessions.
QUIZ_ITEMS_PER_SESSION = 5
REVISE_ITEMS_PER_CONCEPT = 1
DEFAULT_SESSION_INTERVAL_HOURS = 24

# Event type alias for the generator's yield values.
Event = Union[TeachRecord, AttemptRecord, ReviseRecord, "SessionEndRecord"]


@dataclass(frozen=True)
class SessionEndRecord:
    student_id: int
    session_index: int
    time: datetime
    attempts_in_session: int


@dataclass
class TermRunner:
    student: StudentProfile
    concept_graph: ConceptGraph
    item_bank: ItemBank
    bkt_params_by_concept: dict[int, BKTParams]
    start_time: datetime
    n_sessions: int
    session_interval_hours: float = DEFAULT_SESSION_INTERVAL_HOURS
    quiz_items_per_session: int = QUIZ_ITEMS_PER_SESSION
    revise_items_per_concept: int = REVISE_ITEMS_PER_CONCEPT
    seed: int = 0
    # B6: pedagogical-style selector config. The `None` default means
    # `select_explanation_style` uses its module-level defaults.
    explanation_style_config: ExplanationStyleConfig | None = None
    # B5: misconception detector. When set, _detector_hint_for delegates
    # here instead of returning None.
    misconception_detector: MisconceptionDetector | None = None
    # B7: LLM tutor. When set, the teach step generates an explanation
    # in the B6-selected style and stores it in TeachRecord.llm_explanation.
    llm_tutor: LLMTutor | None = None
    # B2 response model: "misconception_weighted" (v2) or "uniform" (v1).
    # Threaded into `simulate_response` on every quiz/revise attempt.
    response_model: str = "misconception_weighted"

    def run(self) -> Iterator[Event]:
        rng = np.random.default_rng(self.seed)
        profile = self.student
        now = self.start_time
        item_ratings: dict[int, float] = {}

        for session_index in range(self.n_sessions):
            attempts_this_session = 0

            if session_index > 0:
                now = now + timedelta(hours=self.session_interval_hours)
                profile = apply_forgetting(profile, now)

            # Teach.
            next_concept = self._pick_next_teach_concept(profile)
            if next_concept is not None:
                teach_style = select_explanation_style(
                    profile, next_concept, config=self.explanation_style_config
                )
                profile, teach_rec = teach(
                    profile, next_concept, now,
                    explanation_style=teach_style,
                    llm_tutor=self.llm_tutor,
                )
                yield teach_rec

            # Quiz on newly-taught concept.
            if next_concept is not None:
                for _ in range(self.quiz_items_per_session):
                    item = select_next_item(profile, self.item_bank, next_concept)
                    if item is None:
                        break
                    profile, record, item_ratings = self._attempt(
                        profile, item, now, rng, item_ratings
                    )
                    yield record
                    attempts_this_session += 1

            # Revise.
            to_revise = select_revision_concepts(profile, now)
            if to_revise:
                yield ReviseRecord(
                    student_id=profile.student_id,
                    concepts=tuple(to_revise),
                    time=now,
                )
                for concept_id in to_revise:
                    for _ in range(self.revise_items_per_concept):
                        item = select_next_item(profile, self.item_bank, concept_id)
                        if item is None:
                            break
                        profile, record, item_ratings = self._attempt(
                            profile, item, now, rng, item_ratings
                        )
                        yield record
                        attempts_this_session += 1

            yield SessionEndRecord(
                student_id=profile.student_id,
                session_index=session_index,
                time=now,
                attempts_in_session=attempts_this_session,
            )

        # Expose the final profile via an attribute so callers can inspect
        # endpoint state without rerunning the loop.
        self.final_profile = profile
        self.final_time = now
        self.final_item_ratings = item_ratings

        # Emit LLM cache statistics once per student term.
        if self.llm_tutor is not None:
            self.llm_tutor.log_cache_stats()

    def _pick_next_teach_concept(self, profile: StudentProfile) -> int | None:
        mastered = {
            c for c, state in profile.bkt_state.items()
            if state.p_known >= _MASTERY_THRESHOLD
        }
        return self.concept_graph.topological_next(mastered)

    def _attempt(
        self,
        profile: StudentProfile,
        item,
        now: datetime,
        rng: np.random.Generator,
        item_ratings: dict[int, float],
    ) -> tuple[StudentProfile, AttemptRecord, dict[int, float]]:
        # Pick the explanation style BEFORE the attempt is resolved — the
        # tutor decides how to frame the item from prior state alone.
        explanation_style = select_explanation_style(
            profile,
            item.concept_id,
            detector_hint=self._detector_hint_for(profile, item),
            config=self.explanation_style_config,
        )
        is_correct, response_time_ms, triggered_misconception_id = simulate_response(
            profile, item, rng, response_model=self.response_model
        )
        current_rating = item_ratings.get(item.item_id, INITIAL_ITEM_ELO)
        bkt = self.bkt_params_by_concept.get(item.concept_id)
        if bkt is None:
            bkt = BKTParams(p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25)
        new_profile, new_rating = apply_practice(
            profile,
            item_id=item.item_id,
            concept_id=item.concept_id,
            is_correct=is_correct,
            item_rating=current_rating,
            bkt_params=bkt,
            now=now,
            response_time_ms=response_time_ms,
            explanation_style=explanation_style,
            triggered_misconception_id=triggered_misconception_id,
        )
        item_ratings = dict(item_ratings)
        item_ratings[item.item_id] = new_rating
        record = new_profile.attempts_history[-1]
        return new_profile, record, item_ratings

    def _detector_hint_for(
        self, profile: StudentProfile, item
    ) -> DetectorHint | None:
        """Return a detector hint from the B5 misconception detector, or None."""
        if self.misconception_detector is None:
            return None
        return self.misconception_detector.predict(profile, item)
