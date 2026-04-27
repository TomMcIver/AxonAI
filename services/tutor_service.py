"""
Shared tutor explanation generation service.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from typing import Optional, Tuple


VALID_EXPLANATION_STYLES = {
    "worked_example",
    "socratic",
    "contrast_with_misconception",
    "analogy",
    "decompose_to_prerequisites",
}

EXPLANATION_PROMPT_TEMPLATES = {
    "worked_example": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "You explain clearly and support confidence without giving away the next answer directly."
        ),
        "user": (
            "A student is learning about {concept_name}. They have attempted this concept {attempt_count} times. "
            "Their misconception is: '{misconception}'. Provide a short worked example that demonstrates the correct method. "
            "Keep it to 3-4 sentences and do not solve a specific pending class question for them."
        ),
    },
    "socratic": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Use Socratic questioning to guide thinking without directly giving final answers."
        ),
        "user": (
            "A student is learning about {concept_name}. They have attempted this concept {attempt_count} times. "
            "Their misconception is: '{misconception}'. Ask 2 short guiding questions, then provide a brief hint. "
            "Keep the response to 3-4 sentences."
        ),
    },
    "contrast_with_misconception": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "You explain concepts clearly and never give away the answer to the next question."
        ),
        "user": (
            "A student is learning about {concept_name}. They have attempted this {attempt_count} times and are still getting it wrong. "
            "Their specific misconception is: '{misconception}'. Explain why this belief is incorrect using a clear counterexample. "
            "Keep it to 3-4 sentences. Do not solve any specific question for them."
        ),
    },
    "analogy": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Use age-appropriate analogies grounded in everyday NZ student experience."
        ),
        "user": (
            "A student is learning about {concept_name}. They have attempted this concept {attempt_count} times. "
            "Their misconception is: '{misconception}'. Explain the concept using one simple analogy and then map the analogy "
            "back to the math idea. Keep it to 3-4 sentences."
        ),
    },
    "decompose_to_prerequisites": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Break hard ideas into prerequisite sub-skills in a calm, stepwise way."
        ),
        "user": (
            "A student is learning about {concept_name}. They have attempted this concept {attempt_count} times. "
            "Their misconception is: '{misconception}'. Decompose this into 2-3 prerequisite ideas they should check first, "
            "then give one concise next step. Keep it to 3-4 sentences."
        ),
    },
}


def get_tutor_cache_key(concept_id: int, misconception: Optional[str], explanation_style: str) -> str:
    normalized_misconception = (misconception or "").strip().lower()
    raw = f"{concept_id}|{normalized_misconception}|{explanation_style}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def call_anthropic_explain(system_prompt: str, user_prompt: str, api_key: str) -> str:
    payload = json.dumps(
        {
            "model": "claude-haiku-4-5",
            "max_tokens": 300,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body.get("content", [])
    parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
    explanation = "".join(parts).strip()
    if not explanation:
        raise RuntimeError("Anthropic returned empty explanation content")
    return explanation


def generate_tutor_explanation(
    cur,
    student_id: int,
    concept_id: int,
    concept_name: str,
    misconception: Optional[str],
    explanation_style: str,
    attempt_count: int,
    year_level: int,
) -> Tuple[str, bool, str]:
    if explanation_style not in VALID_EXPLANATION_STYLES:
        raise ValueError(f"Invalid explanation_style: {explanation_style}")

    cache_key = get_tutor_cache_key(concept_id, misconception, explanation_style)

    cur.execute(
        """
        SELECT content
        FROM messages
        WHERE sender = 'ai_tutor' AND cache_key = %s AND is_cached = true
        ORDER BY sent_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (cache_key,),
    )
    cached = cur.fetchone()
    if cached and cached[0]:
        return str(cached[0]), True, "cache"

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key or not anthropic_api_key.strip():
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    misconception_text = misconception if misconception else "none provided"
    template = EXPLANATION_PROMPT_TEMPLATES[explanation_style]
    system_prompt = template["system"].format(
        concept_name=concept_name,
        misconception=misconception_text,
        attempt_count=attempt_count,
        year_level=year_level,
    )
    user_prompt = template["user"].format(
        concept_name=concept_name,
        misconception=misconception_text,
        attempt_count=attempt_count,
        year_level=year_level,
    )

    model_used = "claude-haiku-4-5"
    explanation = call_anthropic_explain(system_prompt, user_prompt, anthropic_api_key.strip())

    cur.execute(
        """
        SELECT id
        FROM conversations
        WHERE student_id = %s
        ORDER BY started_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (student_id,),
    )
    conv = cur.fetchone()
    if conv:
        conversation_id = conv[0]
    else:
        cur.execute(
            """
            INSERT INTO conversations (
                student_id, class_id, concept_id, total_messages, lightbulb_moment_detected
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (student_id, 1, concept_id, 0, False),
        )
        conversation_id = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(MAX(message_index), 0) AS mx FROM messages WHERE conversation_id = %s",
        (conversation_id,),
    )
    message_index = int(cur.fetchone()[0] or 0) + 1

    cur.execute(
        """
        INSERT INTO messages (
            conversation_id, student_id, sender, content, message_index, concept_id,
            cache_key, is_cached, model_used
        ) VALUES (%s, %s, 'ai_tutor', %s, %s, %s, %s, true, %s)
        """,
        (
            conversation_id,
            student_id,
            explanation,
            message_index,
            concept_id,
            cache_key,
            model_used,
        ),
    )

    return explanation, False, model_used
