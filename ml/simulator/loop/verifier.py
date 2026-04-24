"""Phase 2 PR B9 — rewriter equivalence verifier.

`RewriteVerifier` uses the Anthropic Messages API to check whether a
rewritten quiz question is mathematically equivalent to its original.
It is called on `RewriteRecord` outputs from B8's `QuestionRewriter`.

A rewrite is considered equivalent when the two questions test the same
mathematical concept at the same difficulty level, even if the surface
wording, numbers, or context differ.

Verification result
-------------------

`VerificationResult` carries:
    - `is_equivalent`: bool — the verifier's binary verdict.
    - `confidence`: float in [0, 1] — the model's self-reported certainty.
    - `reason`: str — a short natural-language explanation.
    - `is_simulated`: bool — always True; records may be persisted in
      sim_* tables but never in live RDS tables.

Batch helper
------------

`verify_batch(verifier, records, threshold=0.7)` iterates a list of
`RewriteRecord`s and returns a list of `VerificationResult`s, filtering
out records whose confidence is below `threshold`.

Token budget
------------

Each verification call ≈ 250 input + 80 output tokens on haiku-4-5
≈ $0.000033/call. At one call per rewrite (one per quiz item per session)
and 90k sessions × 5 items: 450k calls × $0.000033 ≈ $15. Combined with
B7 ($4) and B8 ($54), the B7-B9 subtotal is ≈$73, well within $500.
"""

from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Sequence

from ml.simulator.loop.rewriter import RewriteRecord

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 120
_DEFAULT_CONFIDENCE_THRESHOLD = 0.7

_SYSTEM_PROMPT = """\
You are a math education expert. Determine whether two quiz questions test
the same mathematical concept at the same difficulty level.

"Equivalent" means the questions require the same knowledge and reasoning
to answer correctly, even if the wording, numbers, or context differ.

Respond with ONLY a JSON object in this exact format (no markdown fences):
{
  "equivalent": true,
  "confidence": 0.92,
  "reason": "Both questions require solving a two-step linear equation."
}
"confidence" must be a float between 0 and 1.
"reason" must be a single sentence (≤20 words)."""


def _build_user_prompt(original: str, rewritten: str) -> str:
    return f"Question 1 (original): {original}\n\nQuestion 2 (rewritten): {rewritten}"


def _parse_verification(raw: str) -> dict[str, Any]:
    """Parse the model JSON response. Returns a dict with safe defaults on failure."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
        return {
            "equivalent": bool(data.get("equivalent", False)),
            "confidence": float(max(0.0, min(1.0, data.get("confidence", 0.0)))),
            "reason": str(data.get("reason", "")).strip(),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        warnings.warn(
            "RewriteVerifier: could not parse JSON from model response. "
            "Defaulting to non-equivalent with confidence 0.",
            stacklevel=3,
        )
        return {"equivalent": False, "confidence": 0.0, "reason": ""}


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of one equivalence check."""

    original_item_id: int
    concept_id: int
    is_equivalent: bool
    confidence: float
    reason: str
    is_simulated: bool = True


@dataclass
class RewriteVerifier:
    """Checks mathematical equivalence of original ↔ rewritten questions.

    Inject a mock `client` for tests; leave it None to use the live API.
    The `confidence_threshold` is not applied inside this class — callers
    use it to filter results (see `verify_batch`).
    """

    model: str = _DEFAULT_MODEL
    max_tokens: int = _MAX_TOKENS
    client: Any = field(default=None, repr=False)

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client
        import anthropic
        return anthropic.Anthropic()

    def verify(self, record: RewriteRecord) -> VerificationResult:
        """Verify a single `RewriteRecord`. Returns a `VerificationResult`."""
        user_content = _build_user_prompt(
            record.original_question_text,
            record.rewritten_question_text,
        )
        client = self._get_client()
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            parsed = _parse_verification(message.content[0].text)
        except Exception as exc:
            warnings.warn(
                f"RewriteVerifier.verify failed for item {record.original_item_id}: "
                f"{exc!r}. Defaulting to non-equivalent.",
                stacklevel=2,
            )
            parsed = {"equivalent": False, "confidence": 0.0, "reason": ""}

        return VerificationResult(
            original_item_id=record.original_item_id,
            concept_id=record.concept_id,
            is_equivalent=parsed["equivalent"],
            confidence=parsed["confidence"],
            reason=parsed["reason"],
            is_simulated=True,
        )


def verify_batch(
    verifier: RewriteVerifier,
    records: Sequence[RewriteRecord],
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[VerificationResult]:
    """Verify a sequence of RewriteRecords and filter by confidence.

    Returns only results where `confidence >= confidence_threshold`.
    Low-confidence results are discarded (treated as non-actionable); the
    caller should re-run the rewriter on those items or fall back to the
    original item.
    """
    results = []
    for record in records:
        result = verifier.verify(record)
        if result.confidence >= confidence_threshold:
            results.append(result)
    return results
