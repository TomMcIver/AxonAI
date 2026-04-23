"""Phase 2 PR B6 — explanation-style selector.

Picks one of five pedagogical styles to present an item with. The
selector is consumed by the `Teach`/`Quiz`/`Revise` steps (runner
wiring), and the chosen style is stamped onto the `AttemptRecord`
produced by `apply_practice` so downstream validators can measure
"did the right style fire when?" without rerunning the loop.

Design
------

B6 is listed as parallelisable with B1–B5, so the selector must work
*without* the misconception detector (B3/B4) being wired. Rule 1
consumes an optional `DetectorHint`; when absent (the pre-B5 world)
it falls through to the BKT/engagement rules, which only read
`StudentProfile` state that's been populated since Phase 1.

Five rules, ordered — first match wins
--------------------------------------

The Phase 2 spec enumerates five rules and the plan document flags
the ambiguity in how they combine (see `phase_2_plan.md §4.3 concern
#4`: "Rules are ordered in the spec (misconception rule first), so
first-match-wins is the obvious tie-break"). We lock that in here
explicitly and test it.

1. **`contrast_with_misconception`** — detector supplies a
   `DetectorHint` whose confidence ≥ `misconception_confidence_threshold`.
   The tutor reframes the item around refuting that misconception's
   error pattern (Koedinger & Aleven 2007 §3 on self-explanation).
2. **`worked_example`** — BKT `p_known` for the concept is below
   `not_learned_threshold`. The student has not yet acquired the
   procedure; a fully worked example beats a hint (Sweller 1988 on
   cognitive-load theory, Renkl 2014).
3. **`hint`** — the student has a streak of ≥ `streak_wrong_threshold`
   consecutive incorrect attempts on this concept in their immediate
   history. A minimal nudge is cheaper than a full example when they
   have tried and missed.
4. **`analogy`** — the most recent attempt on this concept was slow
   (response time ≥ `slow_response_ms`). Slow but not yet failing
   suggests confusion that a bridging analogy may clear.
5. **`concise_answer`** — default. The student is tracking fine
   (no misconception signal, not in the not-learned zone, no recent
   wrong streak, not stuck on time); a clean terse answer is
   appropriate.

The selector is a pure function of `StudentProfile` + `concept_id` +
optional `DetectorHint` + `ExplanationStyleConfig`. Determinism is
trivial: no RNG, no wall clock.

Constants live here because — like the misconception susceptibility
knobs — they parameterise a published selector's behaviour, not a
runtime tuning surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from ml.simulator.student.profile import StudentProfile

# Style vocabulary — module-level string constants so callers can
# import them by name rather than relying on magic strings. Changes
# to this vocabulary are a simulator-version bump.
CONTRAST_WITH_MISCONCEPTION = "contrast_with_misconception"
WORKED_EXAMPLE = "worked_example"
HINT = "hint"
ANALOGY = "analogy"
CONCISE_ANSWER = "concise_answer"

STYLES = (
    CONTRAST_WITH_MISCONCEPTION,
    WORKED_EXAMPLE,
    HINT,
    ANALOGY,
    CONCISE_ANSWER,
)

# Rule 1 default. Matches the detector's calibrated decision threshold —
# B3/B4 will emit scores in [0, 1]; 0.6 is the operating point chosen
# in the spec ("high-confidence misconception" = ≥ 0.6).
_MISCONCEPTION_CONFIDENCE_THRESHOLD = 0.6
# Rule 2 default. BKT p_known = 0.5 is chance on a binary item; the
# standard "learned" threshold is 0.85 (Corbett & Anderson 1995 §5).
# Students below 0.4 have essentially not started acquiring the
# procedure — the regime where worked examples dominate hints.
_NOT_LEARNED_THRESHOLD = 0.4
# Rule 3 default. Two-in-a-row on one concept is the standard
# intervention trigger (Pelánek 2016 §4.2).
_STREAK_WRONG_THRESHOLD = 2
# Rule 4 default. The simulator's response-time prior is log-normal with
# mu ≈ ln(10 000 ms) = ~10 s; 30 s is well into the right tail (>95th
# percentile for sigma≈0.5), i.e. genuinely slow for a typical student.
_SLOW_RESPONSE_MS = 30_000


@dataclass(frozen=True)
class DetectorHint:
    """Output shape the misconception detector (B3/B4) will publish.

    Defined here so B6 can be written and tested without waiting on
    B3/B4. B5 (detector integration) threads an instance of this into
    `select_explanation_style` before each attempt.
    """

    misconception_id: int
    confidence: float  # in [0, 1]


@dataclass(frozen=True)
class ExplanationStyleConfig:
    """Tunable thresholds for each rule's trigger."""

    misconception_confidence_threshold: float = _MISCONCEPTION_CONFIDENCE_THRESHOLD
    not_learned_threshold: float = _NOT_LEARNED_THRESHOLD
    streak_wrong_threshold: int = _STREAK_WRONG_THRESHOLD
    slow_response_ms: int = _SLOW_RESPONSE_MS


def _recent_attempts_on_concept(
    profile: StudentProfile, concept_id: int, k: int
) -> list:
    """Return up to `k` most-recent attempts on `concept_id`, newest first."""
    out = []
    for record in reversed(profile.attempts_history):
        if record.concept_id == concept_id:
            out.append(record)
            if len(out) >= k:
                break
    return out


def select_explanation_style(
    profile: StudentProfile,
    concept_id: int,
    *,
    detector_hint: DetectorHint | None = None,
    config: ExplanationStyleConfig | None = None,
) -> str:
    """Return one of the five `STYLES` strings. First-match-wins."""
    cfg = config or ExplanationStyleConfig()

    # Rule 1 — misconception refutation wins when the detector is confident.
    if (
        detector_hint is not None
        and detector_hint.confidence >= cfg.misconception_confidence_threshold
    ):
        return CONTRAST_WITH_MISCONCEPTION

    # Rule 2 — worked example when the student hasn't acquired the concept.
    bkt_state = profile.bkt_state.get(concept_id)
    if bkt_state is not None and bkt_state.p_known < cfg.not_learned_threshold:
        return WORKED_EXAMPLE

    # Rule 3 — hint after a streak of consecutive wrong attempts.
    recent = _recent_attempts_on_concept(
        profile, concept_id, cfg.streak_wrong_threshold
    )
    if (
        len(recent) >= cfg.streak_wrong_threshold
        and all(not r.is_correct for r in recent)
    ):
        return HINT

    # Rule 4 — analogy when the most recent attempt was slow.
    if recent and recent[0].response_time_ms >= cfg.slow_response_ms:
        return ANALOGY

    # Rule 5 — default: concise answer for a well-calibrated student.
    return CONCISE_ANSWER
