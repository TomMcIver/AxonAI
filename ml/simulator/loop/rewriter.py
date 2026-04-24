"""Phase 2 PR B8 — question rewriter.

`QuestionRewriter` uses the Anthropic Messages API to produce surface-level
rewrites of quiz questions and their distractors. The mathematical content
(concept, difficulty, misconception structure) is preserved; only wording,
numbers, and context change. This creates item variants for the B11
integration run without introducing new calibration uncertainty.

Two entry points
----------------

**`rewrite(question_text, distractor_texts, ...)`** — core method, takes
raw strings. Returns `(new_question_text, new_distractor_texts)`. Uses a
JSON-structured prompt so the response can be parsed reliably.

**`rewrite_item(item, ...)`** — convenience wrapper around an `Item`. When
`question_text` is None (as it is in the current Phase 1/2 `Item` model),
a synthetic placeholder is generated from the item's IRT parameters. The
return value is a `RewriteRecord` pairing original and rewritten content;
B9 consumes this to verify equivalence.

`is_simulated` invariant
------------------------

Every `RewriteRecord` carries `is_simulated=True`. Callers must propagate
this flag when persisting rewritten items to any storage layer (the Phase 2
non-goal: "No live RDS writes from LLM-generated content").

Token budget
------------

With max_tokens=400 and one call per variant, rewriting costs ≈$0.00012/call
on claude-haiku-4-5. At one variant per quiz item (5 items × 90k sessions),
budget ceiling is ≈$54 — within the $500 Phase 2 cap even at full scale.
"""

from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Sequence

from ml.simulator.data.item_bank import Distractor, Item

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 400

_SYSTEM_PROMPT = """\
You are a math question editor. Your task is to rewrite a quiz question and
its wrong-answer options (distractors) so that:
1. The underlying mathematical concept and difficulty level are preserved exactly.
2. The surface wording, numbers, and context are changed (do not keep the same
   example or the same numerical values if any appear).
3. Each rewritten distractor still corresponds to the same type of mistake as
   the original.

Respond with ONLY a JSON object in this exact format (no markdown fences):
{
  "question": "<rewritten question text>",
  "distractors": ["<distractor 1>", "<distractor 2>", ...]
}
The "distractors" array must have the same length as the input distractors."""


def _build_user_prompt(
    question_text: str,
    distractor_texts: Sequence[str],
    concept_description: str | None,
) -> str:
    lines = []
    if concept_description:
        lines.append(f"Concept: {concept_description}")
    lines.append(f"Original question: {question_text}")
    if distractor_texts:
        lines.append("Original distractors:")
        for i, d in enumerate(distractor_texts, 1):
            lines.append(f"  {i}. {d}")
    return "\n".join(lines)


def _parse_response(raw: str, n_distractors: int) -> tuple[str, tuple[str, ...]]:
    """Extract (question, distractors) from a JSON response string.

    Falls back to the raw string as the question with empty distractors if
    the JSON cannot be parsed, so the caller always gets a usable string.
    """
    # Strip any accidental markdown fences the model might add.
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
        question = str(data.get("question", "")).strip()
        raw_distractors = data.get("distractors", [])
        distractors = tuple(str(d).strip() for d in raw_distractors[:n_distractors])
        if question and len(distractors) == n_distractors:
            return question, distractors
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    warnings.warn(
        "QuestionRewriter: could not parse JSON from model response. "
        "Using raw text as question with empty distractors.",
        stacklevel=3,
    )
    return cleaned or raw, ()


def _synthetic_question(item: Item, concept_description: str | None) -> str:
    """Generate a placeholder question string from IRT parameters.

    Used when a real question text is not available (current Phase 1/2 Item
    model). B11 replaces this with the actual Eedi question text.
    """
    desc = concept_description or f"concept #{item.concept_id}"
    difficulty = (
        "easy" if item.b < -0.5
        else "hard" if item.b > 0.5
        else "moderate"
    )
    return (
        f"[Synthetic] Solve a {difficulty} problem about {desc}. "
        f"(IRT: a={item.a:.2f}, b={item.b:.2f})"
    )


@dataclass(frozen=True)
class RewriteRecord:
    """Pairs an original item's text with its LLM-rewritten variant.

    Both `original_question_text` and `rewritten_question_text` may be
    synthetic placeholders when the underlying `Item` has no real question
    text. `is_simulated` is always True — callers must not persist rewritten
    items to the live RDS layer.
    """

    original_item_id: int
    concept_id: int
    original_question_text: str
    rewritten_question_text: str
    original_distractor_texts: tuple[str, ...]
    rewritten_distractor_texts: tuple[str, ...]
    is_simulated: bool = True

    def to_item_variant(self, new_item_id: int, original_item: Item) -> Item:
        """Build an `Item` variant preserving IRT params and misconception tags.

        Distractor misconception_id values are carried over positionally from
        the original item's distractors. IRT parameters (a, b) are unchanged
        because the rewrite is assumed IRT-invariant (verified by B9).
        """
        orig_distractors = original_item.distractors
        new_distractors = tuple(
            Distractor(
                option_text=text,
                misconception_id=(
                    orig_distractors[i].misconception_id
                    if i < len(orig_distractors)
                    else None
                ),
            )
            for i, text in enumerate(self.rewritten_distractor_texts)
        )
        return Item(
            item_id=new_item_id,
            concept_id=original_item.concept_id,
            a=original_item.a,
            b=original_item.b,
            distractors=new_distractors,
        )


@dataclass
class QuestionRewriter:
    """Generates surface-level rewrites of quiz questions via the Anthropic API.

    Inject a mock `client` for tests; leave it None to use the live API.
    """

    model: str = _DEFAULT_MODEL
    max_tokens: int = _MAX_TOKENS
    client: Any = field(default=None, repr=False)

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client
        import anthropic
        return anthropic.Anthropic()

    def rewrite(
        self,
        question_text: str,
        distractor_texts: Sequence[str],
        concept_description: str | None = None,
    ) -> tuple[str, tuple[str, ...]]:
        """Rewrite question text and distractors, returning (new_q, new_ds).

        Preserves number of distractors and their mathematical error types.
        On API failure, warns and returns the original texts unchanged.
        """
        n = len(distractor_texts)
        user_content = _build_user_prompt(question_text, distractor_texts, concept_description)
        client = self._get_client()
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            raw = message.content[0].text
            return _parse_response(raw, n)
        except Exception as exc:
            warnings.warn(
                f"QuestionRewriter.rewrite failed: {exc!r}. Returning original text.",
                stacklevel=2,
            )
            return question_text, tuple(distractor_texts)

    def rewrite_item(
        self,
        item: Item,
        concept_description: str | None = None,
        question_text: str | None = None,
    ) -> RewriteRecord:
        """Produce a `RewriteRecord` for an `Item`.

        When `question_text` is None (Phase 1/2 Items have no question text),
        a synthetic placeholder is used. B11 will pass real Eedi question text.
        """
        orig_q = question_text or _synthetic_question(item, concept_description)
        orig_ds = tuple(d.option_text for d in item.distractors)

        new_q, new_ds = self.rewrite(orig_q, orig_ds, concept_description)

        return RewriteRecord(
            original_item_id=item.item_id,
            concept_id=item.concept_id,
            original_question_text=orig_q,
            rewritten_question_text=new_q,
            original_distractor_texts=orig_ds,
            rewritten_distractor_texts=new_ds,
            is_simulated=True,
        )
