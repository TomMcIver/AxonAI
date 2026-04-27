"""
Shared tutor explanation generation service.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Optional, Tuple

from openai import OpenAI

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
            "You are learning about {concept_name}. You have attempted this concept {attempt_count} times. "
            "Your misconception is: '{misconception}'. Provide a short worked example that demonstrates the correct method. "
            "Keep it to 3-4 sentences and do not solve a specific pending class question."
        ),
    },
    "socratic": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Use Socratic questioning to guide thinking without directly giving final answers."
        ),
        "user": (
            "You are learning about {concept_name}. You have attempted this concept {attempt_count} times. "
            "Your misconception is: '{misconception}'. Ask 2 short guiding questions, then provide a brief hint. "
            "Keep the response to 3-4 sentences."
        ),
    },
    "contrast_with_misconception": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "You explain concepts clearly and never give away the answer to the next question."
        ),
        "user": (
            "You are learning about {concept_name}. You have attempted this {attempt_count} times and are still getting it wrong. "
            "Your specific misconception is: '{misconception}'. Explain why this belief is incorrect using a clear counterexample. "
            "Keep it to 3-4 sentences. Do not solve any specific pending class question."
        ),
    },
    "analogy": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Use age-appropriate analogies grounded in everyday NZ student experience."
        ),
        "user": (
            "You are learning about {concept_name}. You have attempted this concept {attempt_count} times. "
            "Your misconception is: '{misconception}'. Explain the concept using one simple analogy and then map the analogy "
            "back to the math idea. Keep it to 3-4 sentences."
        ),
    },
    "decompose_to_prerequisites": {
        "system": (
            "You are a mathematics tutor for a Year {year_level} NZ student. "
            "Break hard ideas into prerequisite sub-skills in a calm, stepwise way."
        ),
        "user": (
            "You are learning about {concept_name}. You have attempted this concept {attempt_count} times. "
            "Your misconception is: '{misconception}'. Decompose this into 2-3 prerequisite ideas you should check first, "
            "then give one concise next step. Keep it to 3-4 sentences."
        ),
    },
}


# Research-grounded explanation style selector (first match wins):
# 1) First attempt on concept -> worked_example (Sweller: reduce extraneous load on first exposure).
# 2) Attempt count >= 3 -> decompose_to_prerequisites (Gagne: prerequisite gaps likely).
# 3) Active misconception flagged -> contrast_with_misconception (Chi: refutational text).
# 4) Stuck + low mastery (elo < 1000) -> worked_example (Kirschner: explicit instruction for novices).
# 5) Stuck + mid mastery (1000 <= elo < 1400) -> socratic (Vygotsky: ZPD scaffolding).
# 6) Abstract concept category -> analogy (Gentner: analogical mapping).
# 7) Last message asks "why" -> socratic.
# 8) Default -> worked_example.
def select_explanation_style(student_state: dict) -> str:
    attempt_count = int(student_state.get("attempt_count") or 0)
    elo_rating = float(student_state.get("elo_rating") or 0)
    stuck = bool(student_state.get("stuck"))
    has_active_misconception = bool(student_state.get("has_active_misconception"))
    concept_category = str(student_state.get("concept_category") or "").strip().lower()
    last_message = str(student_state.get("last_message") or "").lower()

    if attempt_count <= 1:
        return "worked_example"
    if attempt_count >= 3:
        return "decompose_to_prerequisites"
    if has_active_misconception:
        return "contrast_with_misconception"
    if stuck and elo_rating < 1000:
        return "worked_example"
    if stuck and 1000 <= elo_rating < 1400:
        return "socratic"
    if concept_category == "abstract":
        return "analogy"
    if "why" in last_message:
        return "socratic"
    return "worked_example"


def get_tutor_cache_key(concept_id: int, misconception: Optional[str], explanation_style: str) -> str:
    normalized_misconception = (misconception or "").strip().lower()
    raw = f"{concept_id}|{normalized_misconception}|{explanation_style}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def call_openai_explain(system_prompt: str, user_prompt: str, api_key: str) -> str:
    response = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=300,
    )
    content = response.choices[0].message.content if response.choices else None
    explanation = (content or "").strip()
    if not explanation:
        raise RuntimeError("OpenAI returned empty explanation content")
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
    cached_content = cached.get("content") if cached else None
    if cached_content:
        return str(cached_content), True, "cache"

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("AI tutor not configured — contact admin to add OPENAI_API_KEY")

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

    model_used = "gpt-4o-mini"
    explanation = call_openai_explain(system_prompt, user_prompt, api_key.strip())

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
        conversation_id = conv["id"]
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
        conversation_id = cur.fetchone()["id"]

    cur.execute(
        "SELECT COALESCE(MAX(message_index), 0) AS mx FROM messages WHERE conversation_id = %s",
        (conversation_id,),
    )
    message_index = int(cur.fetchone()["mx"] or 0) + 1

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
