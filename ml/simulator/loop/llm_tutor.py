"""Phase 2 PR B7 — LLM-powered tutor for the teach step.

`LLMTutor` wraps the Anthropic Messages API to generate a short
pedagogically-styled explanation for a concept before the student's first
quiz attempt in a session. The style is supplied by the B6 selector.

Token budget: Phase 2 spec caps the full B11 run (≈90k sessions) at $500.
With claude-haiku-4-5 at ~$0.25/1M input tokens and max_tokens=150, one
teach call ≈ 200 input + 150 output tokens ≈ $0.000044/call.
One call per session: 90k × $0.000044 ≈ $4 — well within budget.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

from ml.simulator.loop.explanation_style import (
    ANALOGY,
    CONCISE_ANSWER,
    CONTRAST_WITH_MISCONCEPTION,
    HINT,
    WORKED_EXAMPLE,
)

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 150

_SYSTEM_PROMPT = (
    "You are a concise, expert math tutor. "
    "Generate a short (2-3 sentence) teaching explanation for the given concept. "
    "Match the requested pedagogical style exactly."
)

_STYLE_INSTRUCTIONS: dict[str, str] = {
    CONTRAST_WITH_MISCONCEPTION: (
        "Contrast the correct idea with a common misconception. "
        "Name what students often confuse, then clarify why the correct approach differs."
    ),
    WORKED_EXAMPLE: (
        "Show a brief worked example with concrete numbers that illustrates "
        "the concept step by step."
    ),
    HINT: (
        "Give a guiding hint that points the student toward the key insight "
        "without stating the full answer."
    ),
    ANALOGY: (
        "Use a relatable everyday analogy or metaphor to make the abstract concept intuitive."
    ),
    CONCISE_ANSWER: (
        "Give a brief, direct explanation of the concept in plain language."
    ),
}


@dataclass
class LLMTutor:
    """Generates pedagogically-styled explanations via the Anthropic API.

    Inject a mock `client` for tests; leave it None to use the live API.
    The client is lazily constructed on first use so the module imports
    cleanly even when the anthropic package is unavailable.
    """

    model: str = _DEFAULT_MODEL
    max_tokens: int = _MAX_TOKENS
    # Pre-built client for dependency injection / testing.
    client: Any = field(default=None, repr=False)

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client
        import anthropic  # lazy — keeps module importable without the SDK
        return anthropic.Anthropic()

    def generate_explanation(
        self,
        concept_id: int,
        explanation_style: str,
        concept_description: str | None = None,
        misconception_id: int | None = None,
    ) -> str:
        """Return a teaching explanation string.

        Parameters
        ----------
        concept_id:
            Integer concept identifier used verbatim when no description given.
        explanation_style:
            One of the five B6 style constants.
        concept_description:
            Human-readable concept name (e.g. "linear equations"). Falls back
            to "mathematical concept #{concept_id}" when None.
        misconception_id:
            When provided alongside CONTRAST_WITH_MISCONCEPTION style, the
            prompt asks the model to focus the contrast on that misconception.
        """
        desc = concept_description or f"mathematical concept #{concept_id}"
        style_instr = _STYLE_INSTRUCTIONS.get(
            explanation_style, _STYLE_INSTRUCTIONS[CONCISE_ANSWER]
        )
        user_content = f"Concept: {desc}\n\nPedagogical style: {style_instr}"
        if misconception_id is not None and explanation_style == CONTRAST_WITH_MISCONCEPTION:
            user_content += f"\n\nFocus the contrast on misconception #{misconception_id}."

        client = self._get_client()
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            return message.content[0].text
        except Exception as exc:
            warnings.warn(
                f"LLMTutor failed for concept {concept_id} (style={explanation_style}): "
                f"{exc!r}. Returning empty string.",
                stacklevel=2,
            )
            return ""
