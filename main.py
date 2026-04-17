"""
AWS Lambda FastAPI entry point for AxonAI HTTP API (Function URL or API Gateway).

Local Flask app for monorepo development remains in app.py — run that for the
legacy Flask UI. Deploy **this** file as the Lambda handler for the public JSON API.

Handler: `main.handler` (Mangum ASGI adapter).

Environment:
  OPENAI_API_KEY — required for /student/{id}/chat
  AWS_REGION — default ap-southeast-2
  AXONAI_DB_SECRET_ID — default axonai/db/credentials (Secrets Manager)
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.request
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Generator, Optional

import boto3
import psycopg2
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
SECRETS_MANAGER_SECRET_ID = os.environ.get("AXONAI_DB_SECRET_ID", "axonai/db/credentials")
DEFAULT_DB_NAME = os.environ.get("AXONAI_DB_NAME", "postgres")


@lru_cache(maxsize=1)
def _get_db_credentials() -> Dict[str, Any]:
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=SECRETS_MANAGER_SECRET_ID)
    return json.loads(resp["SecretString"])


def _connect_psycopg2():
    creds = _get_db_credentials()
    host = creds.get("host") or creds.get("hostname")
    port = int(creds.get("port", 5432))
    user = creds.get("username") or creds.get("user")
    password = creds.get("password")
    dbname = creds.get("dbname") or creds.get("database") or creds.get("db") or DEFAULT_DB_NAME
    if not user or password is None:
        raise RuntimeError("Database secret must include username and password.")
    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
        connect_timeout=30,
    )


@contextmanager
def get_db() -> Generator[Any, None, None]:
    """Yield a psycopg2 cursor; commit on success, rollback on error."""
    conn = _connect_psycopg2()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _trim_openai_messages(msgs: list) -> list:
    """Keep system prompt + last N user/assistant turns (token safety)."""
    if not msgs:
        return msgs
    if msgs[0].get("role") != "system":
        return msgs[-41:]
    system = msgs[0]
    tail = msgs[1:]
    if len(tail) <= 40:
        return msgs
    return [system] + tail[-40:]


def call_openai_chat_messages(openai_messages: list) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    trimmed = _trim_openai_messages(openai_messages)
    payload = {
        "model": "gpt-4o-mini",
        "messages": trimmed,
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.exception("OpenAI HTTP error: %s %s", e.code, body)
        raise RuntimeError(f"OpenAI error: {e.code}") from e
    return data["choices"][0]["message"]["content"]


def call_openai_chat(system_prompt: str, user_message: str) -> str:
    return call_openai_chat_messages(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )


app = FastAPI(title="AxonAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_root():
    return {"status": "ok", "service": "axonai-api"}


class StudentChatBody(BaseModel):
    message: str = Field(..., min_length=1)
    concept_id: Optional[int] = None
    conversation_id: Optional[int] = None


def _build_system_prompt(first_name: str, learning_style: str) -> str:
    return f"""You are the AxonAI Socratic tutor for New Zealand students.

The learner's first name is {first_name}. Their dominant learning style (when known) is: {learning_style}. Tailor your explanations accordingly (e.g. visual, verbal, kinesthetic cues where appropriate).

Pedagogy:
- Never give the full direct answer immediately. Start with a short guiding question to probe what they already know.
- Then guide them step by step toward the answer.
- If after 2–3 exchanges in this conversation they are clearly still stuck, give one clear, explicit explanation they can follow.
- Stay focused on NCEA Mathematics and Biology curriculum (Years 7–13). Politely redirect off-topic questions back to learning.

You are helpful, encouraging, and concise."""


@app.get("/student/{student_id}/conversations")
def list_student_conversations(student_id: int, limit: int = 30, offset: int = 0):
    """Recent tutor conversations for a student (for resuming sessions)."""
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    try:
        with get_db() as cur:
            cur.execute(
                """
                SELECT c.id, c.started_at, c.total_messages, c.concept_id,
                       c.session_engagement_score, c.lightbulb_moment_detected,
                       cn.name AS concept_name, sub.name AS subject
                FROM conversations c
                LEFT JOIN concepts cn ON cn.id = c.concept_id
                LEFT JOIN subjects sub ON sub.id = cn.subject_id
                WHERE c.student_id = %s
                ORDER BY c.started_at DESC NULLS LAST
                LIMIT %s OFFSET %s
                """,
                (student_id, lim, off),
            )
            rows = cur.fetchall()
        conversations = []
        for r in rows:
            conversations.append(
                {
                    "id": int(r[0]),
                    "started_at": r[1].isoformat() if r[1] else None,
                    "total_messages": int(r[2] or 0),
                    "concept_id": r[3],
                    "session_engagement_score": float(r[4]) if r[4] is not None else None,
                    "lightbulb_moment_detected": bool(r[5]) if r[5] is not None else False,
                    "concept_name": r[6] or "General",
                    "subject": r[7] or "",
                }
            )
        return {"conversations": conversations, "limit": lim, "offset": off}
    except Exception as e:
        logger.exception("list_student_conversations failed: %s", e)
        return {"conversations": [], "limit": lim, "offset": off}


@app.get("/conversation/{conversation_id}/messages")
def get_conversation_messages_route(
    conversation_id: int,
    student_id: Optional[int] = Query(None, description="If set, only return when conversation belongs to this student"),
):
    """Messages for a conversation; pass student_id to enforce ownership."""
    try:
        with get_db() as cur:
            if student_id is not None:
                cur.execute(
                    """
                    SELECT c.id FROM conversations c
                    WHERE c.id = %s AND c.student_id = %s
                    """,
                    (conversation_id, student_id),
                )
                if not cur.fetchone():
                    return JSONResponse(status_code=404, content={"error": "conversation not found"})
            cur.execute(
                """
                SELECT sender, content, message_index, is_lightbulb_moment
                FROM messages
                WHERE conversation_id = %s
                ORDER BY message_index ASC
                """,
                (conversation_id,),
            )
            rows = cur.fetchall()
        out = []
        for sender, content, _idx, lb in rows:
            role = "user" if (sender or "").lower() == "student" else "ai"
            out.append(
                {
                    "role": role,
                    "content": content or "",
                    "lightbulb_moment": bool(lb) if lb is not None else False,
                }
            )
        return {"messages": out}
    except Exception as e:
        logger.exception("get_conversation_messages failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e), "messages": []})


@app.post("/student/{student_id}/chat")
def student_chat(student_id: int, body: StudentChatBody):
    """
    Socratic tutor turn: OpenAI reply + persist conversation + user/AI message rows.
    If conversation_id is set, loads prior messages and sends full context to the model.
    On any failure returns 200 with a friendly message so the SPA does not crash.
    """
    fallback = {
        "response": "Sorry, I'm having trouble right now. Please try again in a moment.",
        "conversation_id": None,
        "lightbulb_detected": False,
    }
    try:
        user_msg = (body.message or "").strip()
        if not user_msg:
            return JSONResponse(status_code=200, content=fallback)

        concept_id: Optional[int] = body.concept_id
        existing_conv_id: Optional[int] = body.conversation_id

        first_name = "there"
        learning_style = "unknown"
        with get_db() as cur:
            cur.execute(
                """
                SELECT s.first_name, COALESCE(slp.dominant_learning_style, 'unknown')
                FROM students s
                LEFT JOIN student_learning_profiles slp ON slp.student_id = s.id
                WHERE s.id = %s
                LIMIT 1
                """,
                (student_id,),
            )
            row = cur.fetchone()
            if row:
                first_name = row[0] or first_name
                learning_style = row[1] or learning_style

        system_prompt = _build_system_prompt(first_name, learning_style)

        history_rows: list = []
        if existing_conv_id is not None:
            with get_db() as cur:
                cur.execute(
                    """
                    SELECT id FROM conversations WHERE id = %s AND student_id = %s
                    """,
                    (existing_conv_id, student_id),
                )
                if not cur.fetchone():
                    existing_conv_id = None
                else:
                    cur.execute(
                        """
                        SELECT sender, content
                        FROM messages
                        WHERE conversation_id = %s
                        ORDER BY message_index ASC
                        """,
                        (existing_conv_id,),
                    )
                    history_rows = cur.fetchall()

        openai_messages: list = [{"role": "system", "content": system_prompt}]
        for sender, content in history_rows:
            s = (sender or "").lower()
            if s == "student":
                openai_messages.append({"role": "user", "content": content or ""})
            elif s == "ai":
                openai_messages.append({"role": "assistant", "content": content or ""})
        openai_messages.append({"role": "user", "content": user_msg})

        ai_reply = call_openai_chat_messages(openai_messages)

        with get_db() as cur:
            if existing_conv_id is None:
                cur.execute(
                    """
                    INSERT INTO conversations (
                        student_id, class_id, concept_id,
                        session_engagement_score, lightbulb_moment_detected, total_messages
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (student_id, 1, concept_id, 0.75, False, 2),
                )
                conv_row = cur.fetchone()
                if not conv_row:
                    raise RuntimeError("Failed to create conversation")
                conversation_id = int(conv_row[0])
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'student', %s, %s)
                    """,
                    (conversation_id, student_id, user_msg, 1),
                )
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'ai', %s, %s)
                    """,
                    (conversation_id, student_id, ai_reply, 2),
                )
            else:
                conversation_id = existing_conv_id
                cur.execute(
                    """
                    SELECT COALESCE(MAX(message_index), 0) FROM messages
                    WHERE conversation_id = %s
                    """,
                    (conversation_id,),
                )
                mx = int(cur.fetchone()[0] or 0)
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'student', %s, %s)
                    """,
                    (conversation_id, student_id, user_msg, mx + 1),
                )
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'ai', %s, %s)
                    """,
                    (conversation_id, student_id, ai_reply, mx + 2),
                )
                cur.execute(
                    """
                    UPDATE conversations
                    SET total_messages = total_messages + 2
                    WHERE id = %s
                    """,
                    (conversation_id,),
                )

        return {
            "response": ai_reply,
            "conversation_id": conversation_id,
            "lightbulb_detected": False,
        }
    except Exception as e:
        logger.exception("student_chat failed: %s", e)
        return JSONResponse(status_code=200, content=fallback)


try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None  # type: ignore[misc, assignment]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
