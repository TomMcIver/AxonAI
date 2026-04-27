#!/usr/bin/env python3
"""
AxonAI Phase 5 — FastAPI Inference API
========================================
Serves real student data from RDS + ML model predictions from S3.
Deploy to AWS Lambda via Mangum, or run locally for dev.

Local dev:
    pip install fastapi uvicorn psycopg2-binary joblib scikit-learn pandas numpy boto3
    export DB_PASSWORD='yourpass'
    python3 axonai_api.py

Endpoints:
    GET  /                                    → API health + stats
    GET  /student/{id}/dashboard              → Full student dashboard
    GET  /student/{id}/summary                → Student summary with top/bottom concepts
    GET  /student/{id}/mastery                → Concept mastery states
    GET  /student/{id}/flags                  → Active flags/misconceptions
    GET  /student/{id}/conversations          → Conversation history
    GET  /student/{id}/predictions            → Model predictions
    GET  /student/{id}/pedagogy               → What teaching approaches work
    GET  /student/{id}/ai-insights            → GPT-4o teacher insights
    GET  /student/{id}/wellbeing              → Wellbeing context
    GET  /student/{id}/pedagogical-memory     → Teaching approach history
    POST /student/{id}/generate-insights      → Generate new GPT-4o insights
    GET  /class/{id}/overview                 → Class-level dashboard for teachers
    GET  /class/{id}/interventions            → Recommended interventions
    GET  /concepts/{subject}                  → Knowledge graph concepts + edges
    POST /predict/risk                        → Live risk prediction
    POST /predict/mastery                     → Live mastery prediction
"""

import os, json, logging, urllib.request, urllib.error, ssl
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import psycopg2
import psycopg2.extras
from services.tutor_service import VALID_EXPLANATION_STYLES, generate_tutor_explanation

# =============================================================================
# APP SETUP
# =============================================================================

app = FastAPI(
    title="AxonAI Inference API",
    description="AI-native school intelligence platform — real-time student analytics and predictions",
    version="1.0.0",
)

# CORS handled by Lambda Function URL config
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("axonai")

# =============================================================================
# DATABASE
# =============================================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "axonai-db-prod.cyxvx9k9pnsx.ap-southeast-2.rds.amazonaws.com"),
    "dbname": os.environ.get("DB_NAME", "axonai"),
    "user": os.environ.get("DB_USER", "axonai_user"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "port": 5432,
    "sslmode": "require",
}

@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# =============================================================================
# ML MODELS (lazy loaded)
# =============================================================================

_models = {}

def get_models():
    """Load models from S3 or local cache."""
    if _models:
        return _models

    import joblib, boto3

    model_dir = "/tmp/models" if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else "trained_models"
    os.makedirs(model_dir, exist_ok=True)

    model_files = ["concept_mastery.joblib","risk_prediction.joblib","engagement.joblib",
                    "misconception.joblib","intervention.joblib","strategy_success.joblib","encoders.joblib"]

    # Download from S3 if not local
    if not os.path.exists(os.path.join(model_dir, "encoders.joblib")):
        try:
            s3 = boto3.client("s3", region_name="ap-southeast-2")
            for fname in model_files:
                s3.download_file("axonai-model-artifacts", f"models/v1/{fname}", os.path.join(model_dir, fname))
            logger.info("Models downloaded from S3")
        except Exception as e:
            logger.warning(f"S3 download failed: {e}")

    for fname in model_files:
        path = os.path.join(model_dir, fname)
        if os.path.exists(path):
            key = fname.replace(".joblib","")
            _models[key] = joblib.load(path)

    logger.info(f"Loaded {len(_models)} models")
    return _models


# =============================================================================
# HEALTH / ROOT
# =============================================================================

@app.get("/")
def root():
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) as n FROM students")
        students = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) as n FROM conversations")
        convos = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) as n FROM messages")
        msgs = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) as n FROM concepts")
        concepts = cur.fetchone()["n"]

    return {
        "status": "healthy",
        "platform": "AxonAI",
        "version": "1.0.0",
        "stats": {
            "students": students,
            "conversations": convos,
            "messages": msgs,
            "concepts": concepts,
        },
        "models": list(get_models().keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# STUDENT DASHBOARD
# =============================================================================

@app.get("/student/{student_id}/dashboard")
def student_dashboard(student_id: int):
    with get_db() as cur:
        # Student info
        cur.execute("""
            SELECT s.id, s.first_name, s.last_name, s.year_level, s.gender, s.ethnicity,
                   s.is_demo_student, s.is_background_student
            FROM students s WHERE s.id = %s
        """, (student_id,))
        student = cur.fetchone()
        if not student:
            raise HTTPException(404, "Student not found")

        # Learning profile
        cur.execute("SELECT * FROM student_learning_profiles WHERE student_id = %s", (student_id,))
        profile = cur.fetchone()

        # Wellbeing
        cur.execute("SELECT * FROM student_wellbeing_context WHERE student_id = %s", (student_id,))
        wellbeing = cur.fetchone()

        # Conversation summary
        cur.execute("""
            SELECT COUNT(*) as total_conversations,
                   AVG(session_engagement_score) as avg_engagement,
                   SUM(CASE WHEN lightbulb_moment_detected THEN 1 ELSE 0 END) as lightbulb_count,
                   SUM(CASE WHEN outcome='resolved' THEN 1 ELSE 0 END) as resolved_count,
                   AVG(total_messages) as avg_messages_per_session
            FROM conversations WHERE student_id = %s
        """, (student_id,))
        conv_summary = cur.fetchone()

        # Quiz summary
        cur.execute("""
            SELECT COUNT(*) as total_quizzes,
                   AVG(score_percentage) as avg_score,
                   MIN(score_percentage) as min_score,
                   MAX(score_percentage) as max_score
            FROM quiz_sessions WHERE student_id = %s
        """, (student_id,))
        quiz_summary = cur.fetchone()

        # Mastery summary
        cur.execute("""
            SELECT AVG(mastery_score) as avg_mastery,
                   MIN(mastery_score) as weakest,
                   MAX(mastery_score) as strongest,
                   COUNT(*) as concepts_assessed
            FROM concept_mastery_states WHERE student_id = %s
        """, (student_id,))
        mastery_summary = cur.fetchone()

        # Active flags
        cur.execute("""
            SELECT COUNT(*) as active_flags
            FROM student_concept_flags WHERE student_id = %s AND is_active = true
        """, (student_id,))
        flags = cur.fetchone()

        # Model predictions
        cur.execute("""
            SELECT model_name, prediction_type, prediction_value, confidence, created_at
            FROM model_predictions WHERE student_id = %s ORDER BY created_at DESC
        """, (student_id,))
        predictions = cur.fetchall()

        # Enrolled classes
        cur.execute("""
            SELECT c.id, c.name, c.year_level, s.name as subject_name
            FROM student_classes sc
            JOIN classes c ON c.id = sc.class_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE sc.student_id = %s AND sc.is_active = true
        """, (student_id,))
        classes = cur.fetchall()

    return {
        "student": _clean(student),
        "profile": _clean(profile),
        "wellbeing": _clean(wellbeing),
        "classes": [_clean(c) for c in classes],
        "summary": {
            "conversations": _clean(conv_summary),
            "quizzes": _clean(quiz_summary),
            "mastery": _clean(mastery_summary),
            "active_flags": flags["active_flags"] if flags else 0,
        },
        "predictions": [_clean(p) for p in predictions],
    }


# =============================================================================
# STUDENT SUMMARY (NEW - Top/Bottom 3 Concepts)
# =============================================================================

@app.get("/student/{student_id}/summary")
def get_student_summary(student_id: int):
    """
    Returns student's overall class scores + top/bottom 3 concepts per class
    """
    try:
        with get_db() as cur:
            # Get student info and class scores
            cur.execute("""
                SELECT 
                  s.id, s.first_name, s.last_name,
                  c.id as class_id, c.name as class_name,
                  CAST(AVG(cms.mastery_score) * 100 AS NUMERIC(5,1)) as overall_score
                FROM students s
                CROSS JOIN classes c
                LEFT JOIN concept_mastery_states cms ON s.id = cms.student_id
                LEFT JOIN class_concepts cc ON cms.concept_id = cc.concept_id AND cc.class_id = c.id
                WHERE s.id = %s AND cc.class_id IS NOT NULL
                GROUP BY s.id, s.first_name, s.last_name, c.id, c.name
            """, (student_id,))
            
            result = cur.fetchall()
            
            if not result:
                raise HTTPException(status_code=404, detail="Student not found")
            
            first_row = result[0]
            student_name = f"{first_row['first_name']} {first_row['last_name']}"
            
            classes_data = []
            for row in result:
                class_id = row['class_id']
                
                # Get top 3 mastered concepts (85%+)
                cur.execute("""
                    SELECT c.id, c.name, CAST(cms.mastery_score * 100 AS NUMERIC(5,1)) as mastery_score
                    FROM concept_mastery_states cms
                    JOIN concepts c ON cms.concept_id = c.id
                    JOIN class_concepts cc ON c.id = cc.concept_id
                    WHERE cms.student_id = %s AND cc.class_id = %s
                      AND cms.mastery_score >= 0.85
                    ORDER BY cms.mastery_score DESC
                    LIMIT 3
                """, (student_id, class_id))
                
                top_3 = cur.fetchall()
                
                # Get bottom 3 struggling concepts (<50%)
                cur.execute("""
                    SELECT c.id, c.name, CAST(cms.mastery_score * 100 AS NUMERIC(5,1)) as mastery_score
                    FROM concept_mastery_states cms
                    JOIN concepts c ON cms.concept_id = c.id
                    JOIN class_concepts cc ON c.id = cc.concept_id
                    WHERE cms.student_id = %s AND cc.class_id = %s
                      AND cms.mastery_score < 0.5
                    ORDER BY cms.mastery_score ASC
                    LIMIT 3
                """, (student_id, class_id))
                
                bottom_3 = cur.fetchall()
                
                classes_data.append({
                    "class_id": class_id,
                    "class_name": row['class_name'],
                    "overall_score": float(row['overall_score']) if row['overall_score'] else 0,
                    "top_3_mastered": [
                        {
                            "concept_id": c['id'],
                            "name": c['name'],
                            "mastery_score": float(c['mastery_score'])
                        }
                        for c in top_3
                    ],
                    "bottom_3_struggling": [
                        {
                            "concept_id": c['id'],
                            "name": c['name'],
                            "mastery_score": float(c['mastery_score'])
                        }
                        for c in bottom_3
                    ]
                })
            
            return {
                "student_id": student_id,
                "student_name": student_name,
                "classes": classes_data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MASTERY
# =============================================================================

@app.get("/student/{student_id}/mastery")
def student_mastery(student_id: int, subject: Optional[str] = None):
    with get_db() as cur:
        query = """
            SELECT cm.concept_id, c.name as concept_name, s.name as subject,
                   cm.mastery_score, cm.confidence, cm.evidence_count,
                   cm.last_quiz_score, cm.last_conversation_outcome, cm.trend,
                   cm.first_assessed_at, cm.last_updated_at,
                   c.difficulty_level, c.concept_type
            FROM concept_mastery_states cm
            JOIN concepts c ON c.id = cm.concept_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE cm.student_id = %s
        """
        params = [student_id]
        if subject:
            query += " AND s.name ILIKE %s"
            params.append(f"%{subject}%")
        query += " ORDER BY cm.mastery_score ASC"

        cur.execute(query, params)
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(404, "No mastery data found")

    return {
        "student_id": student_id,
        "total_concepts": len(rows),
        "avg_mastery": round(sum(r["mastery_score"] for r in rows) / len(rows), 3),
        "concepts": [_clean(r) for r in rows],
    }


# =============================================================================
# FLAGS
# =============================================================================

@app.get("/student/{student_id}/flags")
def student_flags(student_id: int, active_only: bool = True):
    with get_db() as cur:
        query = """
            SELECT f.id, f.concept_id, c.name as concept_name, s.name as subject,
                   f.flag_type, f.flag_detail, f.is_active, f.recommended_intervention,
                   f.raised_at, f.resolved_at,
                   rc.name as root_cause_concept_name
            FROM student_concept_flags f
            JOIN concepts c ON c.id = f.concept_id
            JOIN subjects s ON s.id = c.subject_id
            LEFT JOIN concepts rc ON rc.id = f.root_cause_concept_id
            WHERE f.student_id = %s
        """
        params = [student_id]
        if active_only:
            query += " AND f.is_active = true"
        query += " ORDER BY f.raised_at DESC"

        cur.execute(query, params)
        rows = cur.fetchall()

    return {
        "student_id": student_id,
        "total_flags": len(rows),
        "flags": [_clean(r) for r in rows],
    }


# =============================================================================
# CONVERSATIONS
# =============================================================================

@app.get("/student/{student_id}/conversations")
def student_conversations(student_id: int, limit: int = 20, offset: int = 0):
    with get_db() as cur:
        cur.execute("""
            SELECT conv.id, conv.concept_id, c.name as concept_name, s.name as subject,
                   conv.started_at, conv.ended_at, conv.total_messages,
                   conv.lightbulb_moment_detected, conv.session_engagement_score,
                   conv.primary_teaching_approach, conv.outcome
            FROM conversations conv
            JOIN concepts c ON c.id = conv.concept_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE conv.student_id = %s
            ORDER BY conv.started_at DESC
            LIMIT %s OFFSET %s
        """, (student_id, limit, offset))
        convos = cur.fetchall()

        cur.execute("SELECT COUNT(*) as n FROM conversations WHERE student_id = %s", (student_id,))
        total = cur.fetchone()["n"]

    return {
        "student_id": student_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "conversations": [_clean(c) for c in convos],
    }


@app.get("/conversation/{conversation_id}/messages")
def conversation_messages(conversation_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT m.id, m.sender, m.content, m.message_index, m.sent_at,
                   m.response_time_seconds, m.teaching_approach,
                   m.is_lightbulb_moment, m.frustration_signal, m.engagement_signal,
                   m.word_count
            FROM messages m
            WHERE m.conversation_id = %s
            ORDER BY m.message_index ASC
        """, (conversation_id,))
        msgs = cur.fetchall()

        cur.execute("""
            SELECT conv.*, c.name as concept_name, s.name as subject
            FROM conversations conv
            JOIN concepts c ON c.id = conv.concept_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE conv.id = %s
        """, (conversation_id,))
        conv = cur.fetchone()

    if not conv:
        raise HTTPException(404, "Conversation not found")

    return {
        "conversation": _clean(conv),
        "messages": [_clean(m) for m in msgs],
    }


# =============================================================================
# PREDICTIONS
# =============================================================================

@app.get("/student/{student_id}/predictions")
def student_predictions(student_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT model_name, prediction_type, prediction_value, confidence, created_at
            FROM model_predictions WHERE student_id = %s ORDER BY created_at DESC
        """, (student_id,))
        rows = cur.fetchall()

    return {
        "student_id": student_id,
        "predictions": [_clean(r) for r in rows],
    }


# =============================================================================
# PEDAGOGY
# =============================================================================

@app.get("/student/{student_id}/pedagogy")
def student_pedagogy(student_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT teaching_approach, concept_type, success_count, attempt_count,
                   success_rate, avg_messages_to_lightbulb, last_used_at
            FROM pedagogical_memory
            WHERE student_id = %s
            ORDER BY success_rate DESC
        """, (student_id,))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(404, "No pedagogical data found")

    best = rows[0]
    return {
        "student_id": student_id,
        "best_approach": best["teaching_approach"],
        "best_success_rate": float(best["success_rate"]),
        "approaches": [_clean(r) for r in rows],
    }


# =============================================================================
# AI INSIGHTS (GPT-4o generated teacher summaries)
# =============================================================================

@app.get("/student/{student_id}/ai-insights")
def get_ai_insights(student_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT student_summary, risk_narrative,
                   recommended_interventions, teaching_approach_advice,
                   generated_at, model_used
            FROM teacher_ai_insights
            WHERE student_id = %s
            ORDER BY generated_at DESC LIMIT 1
        """, (student_id,))
        row = cur.fetchone()
    if not row:
        return {"insights": None}
    return {"insights": _clean(row)}


@app.post("/student/{student_id}/generate-insights")
def generate_insights_endpoint(student_id: int):
    """Generate GPT-4o AI insights for a student and save to database"""
    try:
        # Step 1: Get student data
        with get_db() as cur:
            cur.execute("""
                SELECT first_name, last_name FROM students WHERE id = %s
            """, (student_id,))
            student_row = cur.fetchone()
            
        if not student_row:
            raise HTTPException(404, f"Student {student_id} not found")
        
        fname = student_row["first_name"]
        lname = student_row["last_name"]
        
        # Step 2: Call GPT-4o with minimal context
        prompt = f"""Generate 4 JSON fields for {fname} {lname}:
Return ONLY this JSON (no markdown):
{{"student_summary":"Brief summary", "risk_narrative":"Risk assessment", "recommended_interventions":"Suggestions", "teaching_approach_advice":"Teaching tips"}}"""

        api_key = os.environ.get('OPENAI_API_KEY')
        payload = json.dumps({
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }).encode('utf-8')
        
        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['choices'][0]['message']['content']
            start = text.find('{')
            end = text.rfind('}') + 1
            insights = json.loads(text[start:end])
        
        # Step 3: Save to database
        with get_db() as cur:
            cur.execute("SELECT id FROM teacher_ai_insights WHERE student_id = %s", (student_id,))
            exists = cur.fetchone()
            now = datetime.now(timezone.utc).isoformat()
            
            if exists:
                cur.execute("""UPDATE teacher_ai_insights SET 
                    student_summary=%s, risk_narrative=%s, 
                    recommended_interventions=%s, teaching_approach_advice=%s,
                    model_used='gpt-4o', generated_at=%s 
                    WHERE student_id=%s""",
                    (insights.get('student_summary'), insights.get('risk_narrative'), 
                     insights.get('recommended_interventions'), insights.get('teaching_approach_advice'), 
                     now, student_id))
            else:
                cur.execute("""INSERT INTO teacher_ai_insights 
                    (student_id, teacher_id, class_id, student_summary, risk_narrative, recommended_interventions, 
                     teaching_approach_advice, model_used, generated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'gpt-4o', %s)""",
                    (student_id, 1, 1, insights.get('student_summary'), insights.get('risk_narrative'),
                     insights.get('recommended_interventions'), insights.get('teaching_approach_advice'), now))
        
        return {
            'success': True,
            'student': f"{fname} {lname}",
            'message': f"{'Updated' if exists else 'Inserted'} insights for student {student_id}",
            'insights': insights
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


# =============================================================================
# WELLBEING CONTEXT
# =============================================================================

@app.get("/student/{student_id}/wellbeing")
def get_wellbeing(student_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT has_learning_support_plan, learning_support_details,
                   has_medical_condition, medical_details,
                   home_situation_flag, home_situation_notes,
                   is_esol, attendance_percentage
            FROM student_wellbeing_context
            WHERE student_id = %s
        """, (student_id,))
        row = cur.fetchone()
    if not row:
        return {"wellbeing": None}
    return {"wellbeing": _clean(row)}


# =============================================================================
# PEDAGOGICAL MEMORY
# =============================================================================

@app.get("/student/{student_id}/pedagogical-memory")
def get_pedagogical_memory(student_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT teaching_approach, concept_type, success_count, attempt_count,
                   success_rate, avg_messages_to_lightbulb, last_used_at,
                   last_successful_at
            FROM pedagogical_memory
            WHERE student_id = %s
            ORDER BY success_rate DESC
        """, (student_id,))
        rows = cur.fetchall()
    return {
        "student_id": student_id,
        "approaches": [_clean(r) for r in rows]
    }


# =============================================================================
# CLASS OVERVIEW (Teacher Dashboard)
# =============================================================================

@app.get("/class/{class_id}/overview")
def class_overview(class_id: int):
    with get_db() as cur:
        # Class info
        cur.execute("""
            SELECT c.id, c.name, c.year_level, c.academic_year, s.name as subject
            FROM classes c JOIN subjects s ON s.id = c.subject_id
            WHERE c.id = %s
        """, (class_id,))
        cls = cur.fetchone()
        if not cls:
            raise HTTPException(404, "Class not found")

        # All students in class with key metrics
        cur.execute("""
            SELECT s.id as student_id, s.first_name, s.last_name, s.year_level,
                   p.overall_engagement_score, p.overall_risk_score, p.overall_mastery_trend,
                   p.total_interactions, p.dominant_learning_style,
                   w.attendance_percentage,
                   (SELECT AVG(mastery_score) FROM concept_mastery_states WHERE student_id = s.id) as avg_mastery,
                   (SELECT AVG(score_percentage) FROM quiz_sessions WHERE student_id = s.id) as avg_quiz_score,
                   (SELECT COUNT(*) FROM student_concept_flags WHERE student_id = s.id AND is_active = true) as active_flags
            FROM student_classes sc
            JOIN students s ON s.id = sc.student_id
            LEFT JOIN student_learning_profiles p ON p.student_id = s.id
            LEFT JOIN student_wellbeing_context w ON w.student_id = s.id
            WHERE sc.class_id = %s AND sc.is_active = true
            ORDER BY p.overall_risk_score DESC NULLS LAST
        """, (class_id,))
        students = cur.fetchall()

        # Class-level stats
        cur.execute("""
            SELECT COUNT(DISTINCT conv.student_id) as active_students,
                   COUNT(*) as total_conversations,
                   AVG(conv.session_engagement_score) as avg_engagement,
                   SUM(CASE WHEN conv.outcome='resolved' THEN 1 ELSE 0 END)::float /
                   NULLIF(COUNT(*),0) as resolve_rate
            FROM conversations conv
            WHERE conv.class_id = %s
        """, (class_id,))
        class_stats = cur.fetchone()

    # Categorize students
    at_risk = [s for s in students if s["overall_risk_score"] and s["overall_risk_score"] > 0.4]
    improving = [s for s in students if s["overall_mastery_trend"] == "improving"]
    declining = [s for s in students if s["overall_mastery_trend"] == "declining"]

    return {
        "class": _clean(cls),
        "class_stats": _clean(class_stats),
        "student_count": len(students),
        "at_risk_count": len(at_risk),
        "improving_count": len(improving),
        "declining_count": len(declining),
        "students": [_clean(s) for s in students],
    }


@app.get("/class/{class_id}/interventions")
def class_interventions(class_id: int):
    with get_db() as cur:
        cur.execute("""
            SELECT ti.id, ti.intervention_type, ti.student_ids,
                   c.name as concept_name, ti.recommended_action,
                   ti.likelihood_of_success, ti.students_sharing_gap,
                   ti.teacher_actioned, ti.created_at
            FROM teacher_interventions ti
            LEFT JOIN concepts c ON c.id = ti.concept_id
            WHERE ti.class_id = %s
            ORDER BY ti.created_at DESC
        """, (class_id,))
        rows = cur.fetchall()

    return {
        "class_id": class_id,
        "total_interventions": len(rows),
        "interventions": [_clean(r) for r in rows],
    }


# =============================================================================
# KNOWLEDGE GRAPH
# =============================================================================

@app.get("/concepts/{subject}")
def get_concepts(subject: str):
    with get_db() as cur:
        cur.execute("""
            SELECT c.id, c.name, c.description, c.difficulty_level,
                   c.year_level_introduced, c.concept_type
            FROM concepts c
            JOIN subjects s ON s.id = c.subject_id
            WHERE s.name ILIKE %s
            ORDER BY c.id
        """, (f"%{subject}%",))
        concepts = cur.fetchall()

        cur.execute("""
            SELECT cp.concept_id, cp.prerequisite_concept_id, cp.strength
            FROM concept_prerequisites cp
            JOIN concepts c ON c.id = cp.concept_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE s.name ILIKE %s
        """, (f"%{subject}%",))
        edges = cur.fetchall()

    return {
        "subject": subject,
        "total_concepts": len(concepts),
        "total_edges": len(edges),
        "concepts": [_clean(c) for c in concepts],
        "prerequisites": [_clean(e) for e in edges],
    }


# =============================================================================
# LIVE PREDICTIONS
# =============================================================================

class RiskPredictionRequest(BaseModel):
    student_id: int


class QuizSubmitRequest(BaseModel):
    student_id: int
    quiz_question_id: int
    student_answer: str
    concept_id: int
    time_taken_seconds: Optional[float] = None


class StudentChatBody(BaseModel):
    message: str
    concept_id: Optional[int] = None
    conversation_id: Optional[int] = None


STUCK_KEYWORDS = (
    "stuck",
    "don't understand",
    "confused",
    "help",
    "explain",
    "why",
    "how does",
    "what is",
    "i don't get",
)


def _message_indicates_stuck(message: str) -> bool:
    text = (message or "").lower()
    return any(keyword in text for keyword in STUCK_KEYWORDS)


def _select_explanation_style(message: str, misconception: Optional[str]) -> str:
    text = (message or "").lower()
    if misconception:
        return "contrast_with_misconception"
    if "example" in text or "show me" in text:
        return "worked_example"
    if "why" in text:
        return "socratic"
    return "worked_example"


def _build_chat_system_prompt(first_name: str, learning_style: str) -> str:
    return f"""You are the AxonAI Socratic tutor for New Zealand students.

The learner's first name is {first_name}. Their dominant learning style (when known) is: {learning_style}. Tailor your explanations accordingly (e.g. visual, verbal, kinesthetic cues where appropriate).

Pedagogy:
- Never give the full direct answer immediately. Start with a short guiding question to probe what they already know.
- Then guide them step by step toward the answer.
- If after 2–3 exchanges in this conversation they are clearly still stuck, give one clear, explicit explanation they can follow.
- Stay focused on NCEA Mathematics and Biology curriculum (Years 7–13). Politely redirect off-topic questions back to learning.

You are helpful, encouraging, and concise."""


def _trim_openai_messages(msgs: list) -> list:
    if not msgs:
        return msgs
    if msgs[0].get("role") != "system":
        return msgs[-41:]
    system = msgs[0]
    tail = msgs[1:]
    if len(tail) <= 40:
        return msgs
    return [system] + tail[-40:]


def _call_openai_chat_messages(openai_messages: list) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    payload = {
        "model": "gpt-4o-mini",
        "messages": _trim_openai_messages(openai_messages),
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
    with urllib.request.urlopen(req, context=ctx, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


@app.post("/quiz/submit")
def submit_quiz_answer(req: QuizSubmitRequest):
    detected_misconception: Optional[str] = None
    misconception_confidence: Optional[float] = None

    with get_db() as cur:
        cur.execute(
            """
            SELECT id, concept_id, question_text, correct_answer
            FROM quiz_questions
            WHERE id = %s
            """,
            (req.quiz_question_id,),
        )
        question = cur.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Quiz question not found")

        correct_answer = question.get("correct_answer")
        student_answer = req.student_answer.strip()
        is_correct = student_answer == (correct_answer or "").strip()

        cur.execute(
            """
            UPDATE quiz_questions
            SET student_answer = %s,
                is_correct = %s,
                time_taken_seconds = %s
            WHERE id = %s
            """,
            (student_answer, is_correct, req.time_taken_seconds, req.quiz_question_id),
        )

        if not is_correct:
            concept_name = None
            cur.execute("SELECT name FROM concepts WHERE id = %s", (req.concept_id,))
            concept_row = cur.fetchone()
            if concept_row:
                concept_name = concept_row.get("name")

            # Detector failures must never break quiz submission.
            try:
                from misconception_adapter import detect_misconception

                detected_misconception, misconception_confidence = detect_misconception(
                    question_text=question.get("question_text"),
                    wrong_answer=student_answer,
                    concept_name=concept_name or "",
                )
            except Exception as exc:
                logger.warning("Misconception adapter import/call failed: %s", exc)
                detected_misconception = None
                misconception_confidence = None

            if (
                detected_misconception
                and misconception_confidence is not None
                and float(misconception_confidence) > 0.5
            ):
                misconception_confidence = float(misconception_confidence)
                cur.execute(
                    """
                    SELECT id
                    FROM student_concept_flags
                    WHERE student_id = %s
                      AND concept_id = %s
                      AND flag_type = 'misconception'
                      AND flag_detail = %s
                      AND is_active = true
                    LIMIT 1
                    """,
                    (req.student_id, req.concept_id, detected_misconception),
                )
                existing_flag = cur.fetchone()

                if existing_flag:
                    cur.execute(
                        """
                        UPDATE student_concept_flags
                        SET raised_at = NOW()
                        WHERE id = %s
                        """,
                        (existing_flag["id"],),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO student_concept_flags (
                            student_id,
                            concept_id,
                            flag_type,
                            flag_detail,
                            root_cause_concept_id,
                            raised_at,
                            is_active,
                            recommended_intervention
                        ) VALUES (%s, %s, 'misconception', %s, %s, NOW(), true, NULL)
                        """,
                        (
                            req.student_id,
                            req.concept_id,
                            detected_misconception,
                            req.concept_id,
                        ),
                    )
            else:
                detected_misconception = None
                misconception_confidence = None

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "detected_misconception": detected_misconception,
        "misconception_confidence": misconception_confidence,
    }


@app.post("/quiz/submit")
def submit_quiz_answer(req: QuizSubmitRequest):
    detected_misconception: Optional[str] = None
    misconception_confidence: Optional[float] = None

    with get_db() as cur:
        cur.execute(
            """
            SELECT id, concept_id, question_text, correct_answer
            FROM quiz_questions
            WHERE id = %s
            """,
            (req.quiz_question_id,),
        )
        question = cur.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Quiz question not found")

        correct_answer = question.get("correct_answer")
        student_answer = req.student_answer.strip()
        is_correct = student_answer == (correct_answer or "").strip()

        cur.execute(
            """
            UPDATE quiz_questions
            SET student_answer = %s,
                is_correct = %s,
                time_taken_seconds = %s
            WHERE id = %s
            """,
            (student_answer, is_correct, req.time_taken_seconds, req.quiz_question_id),
        )

        if not is_correct:
            concept_name = None
            cur.execute("SELECT name FROM concepts WHERE id = %s", (req.concept_id,))
            concept_row = cur.fetchone()
            if concept_row:
                concept_name = concept_row.get("name")

            # Detector failures must never break quiz submission.
            try:
                from misconception_adapter import detect_misconception

                detected_misconception, misconception_confidence = detect_misconception(
                    question_text=question.get("question_text"),
                    wrong_answer=student_answer,
                    concept_name=concept_name or "",
                )
            except Exception as exc:
                logger.warning("Misconception adapter import/call failed: %s", exc)
                detected_misconception = None
                misconception_confidence = None

            if (
                detected_misconception
                and misconception_confidence is not None
                and float(misconception_confidence) > 0.5
            ):
                misconception_confidence = float(misconception_confidence)
                cur.execute(
                    """
                    SELECT id
                    FROM student_concept_flags
                    WHERE student_id = %s
                      AND concept_id = %s
                      AND flag_type = 'misconception'
                      AND flag_detail = %s
                      AND is_active = true
                    LIMIT 1
                    """,
                    (req.student_id, req.concept_id, detected_misconception),
                )
                existing_flag = cur.fetchone()

                if existing_flag:
                    cur.execute(
                        """
                        UPDATE student_concept_flags
                        SET raised_at = NOW()
                        WHERE id = %s
                        """,
                        (existing_flag["id"],),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO student_concept_flags (
                            student_id,
                            concept_id,
                            flag_type,
                            flag_detail,
                            root_cause_concept_id,
                            raised_at,
                            is_active,
                            recommended_intervention
                        ) VALUES (%s, %s, 'misconception', %s, %s, NOW(), true, NULL)
                        """,
                        (
                            req.student_id,
                            req.concept_id,
                            detected_misconception,
                            req.concept_id,
                        ),
                    )
            else:
                detected_misconception = None
                misconception_confidence = None

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "detected_misconception": detected_misconception,
        "misconception_confidence": misconception_confidence,
    }

@app.post("/predict/risk")
def predict_risk(req: RiskPredictionRequest):
    models = get_models()
    if "risk_prediction" not in models:
        raise HTTPException(503, "Risk model not loaded")

    model_data = models["risk_prediction"]
    encoders = models.get("encoders", {})

    with get_db() as cur:
        features = _build_student_features(cur, req.student_id, encoders)

    if not features:
        raise HTTPException(404, "Student not found or insufficient data")

    import pandas as pd
    X = pd.DataFrame([features])[model_data["features"]]
    pred = model_data["model"].predict(X)[0]
    prob = model_data["model"].predict_proba(X)[0]

    return {
        "student_id": req.student_id,
        "at_risk": bool(pred),
        "risk_probability": round(float(prob[1]), 4),
        "confidence": round(float(max(prob)), 4),
        "model_accuracy": model_data.get("test_accuracy", "N/A"),
    }


@app.post("/student/{student_id}/chat")
def student_chat(student_id: int, body: StudentChatBody):
    fallback = {
        "response": "Sorry, I'm having trouble right now. Please try again in a moment.",
        "conversation_id": None,
        "lightbulb_detected": False,
        "tutor_explanation": None,
        "cache_hit": False,
    }
    try:
        user_msg = (body.message or "").strip()
        if not user_msg:
            return fallback

        concept_id = body.concept_id
        existing_conv_id = body.conversation_id

        first_name = "there"
        learning_style = "unknown"
        year_level = 10
        with get_db() as cur:
            cur.execute(
                """
                SELECT s.first_name,
                       COALESCE(slp.dominant_learning_style, 'unknown') AS learning_style,
                       COALESCE(s.year_level, 10) AS year_level
                FROM students s
                LEFT JOIN student_learning_profiles slp ON slp.student_id = s.id
                WHERE s.id = %s
                LIMIT 1
                """,
                (student_id,),
            )
            row = cur.fetchone()
            if row:
                first_name = row["first_name"] or first_name
                learning_style = row["learning_style"] or learning_style
                year_level = int(row["year_level"] or year_level)

        system_prompt = _build_chat_system_prompt(first_name, learning_style)

        history_rows = []
        if existing_conv_id is not None:
            with get_db() as cur:
                cur.execute(
                    "SELECT id FROM conversations WHERE id = %s AND student_id = %s",
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

        openai_messages = [{"role": "system", "content": system_prompt}]
        for row in history_rows:
            sender = (row["sender"] or "").lower()
            if sender == "student":
                openai_messages.append({"role": "user", "content": row["content"] or ""})
            elif sender == "ai":
                openai_messages.append({"role": "assistant", "content": row["content"] or ""})
        openai_messages.append({"role": "user", "content": user_msg})

        ai_reply = _call_openai_chat_messages(openai_messages)
        tutor_explanation = None
        tutor_cache_hit = False

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
                conversation_id = int(cur.fetchone()["id"])
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'student', %s, 1)
                    """,
                    (conversation_id, student_id, user_msg),
                )
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, student_id, sender, content, message_index
                    )
                    VALUES (%s, %s, 'ai', %s, 2)
                    """,
                    (conversation_id, student_id, ai_reply),
                )
            else:
                conversation_id = existing_conv_id
                cur.execute(
                    "SELECT COALESCE(MAX(message_index), 0) AS mx FROM messages WHERE conversation_id = %s",
                    (conversation_id,),
                )
                mx = int(cur.fetchone()["mx"] or 0)
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
                    "UPDATE conversations SET total_messages = total_messages + 2 WHERE id = %s",
                    (conversation_id,),
                )

            try:
                current_concept_id = concept_id
                if current_concept_id is None:
                    cur.execute(
                        "SELECT concept_id FROM conversations WHERE id = %s AND student_id = %s LIMIT 1",
                        (conversation_id, student_id),
                    )
                    concept_row = cur.fetchone()
                    current_concept_id = concept_row["concept_id"] if concept_row else None

                has_active_current_flag = False
                if current_concept_id is not None:
                    cur.execute(
                        """
                        SELECT id
                        FROM student_concept_flags
                        WHERE student_id = %s
                          AND concept_id = %s
                          AND is_active = true
                        ORDER BY raised_at DESC NULLS LAST, id DESC
                        LIMIT 1
                        """,
                        (student_id, current_concept_id),
                    )
                    has_active_current_flag = cur.fetchone() is not None

                student_is_stuck = _message_indicates_stuck(user_msg) or has_active_current_flag
                if student_is_stuck:
                    if current_concept_id is not None:
                        cur.execute(
                            """
                            SELECT concept_id, flag_detail
                            FROM student_concept_flags
                            WHERE student_id = %s
                              AND concept_id = %s
                              AND is_active = true
                            ORDER BY raised_at DESC NULLS LAST, id DESC
                            LIMIT 1
                            """,
                            (student_id, current_concept_id),
                        )
                        latest_flag = cur.fetchone()
                        if latest_flag:
                            tutor_concept_id = latest_flag["concept_id"]
                            misconception = (
                                (latest_flag["flag_detail"] or "").strip()
                                if latest_flag and latest_flag.get("flag_detail")
                                else None
                            )

                            tutor_concept_name = None
                            if tutor_concept_id is not None:
                                cur.execute("SELECT name FROM concepts WHERE id = %s", (tutor_concept_id,))
                                concept_name_row = cur.fetchone()
                                tutor_concept_name = concept_name_row["name"] if concept_name_row else None

                            if tutor_concept_id is not None and tutor_concept_name:
                                cur.execute(
                                    """
                                    SELECT COUNT(*)
                                    FROM messages m
                                    JOIN conversations c ON c.id = m.conversation_id
                                    WHERE m.student_id = %s
                                      AND m.sender = 'student'
                                      AND c.concept_id = %s
                                    """,
                                    (student_id, tutor_concept_id),
                                )
                                attempt_count = max(1, int(cur.fetchone()["count"] or 0))
                                explanation_style = _select_explanation_style(user_msg, misconception)
                                tutor_explanation, tutor_cache_hit, _model_used = generate_tutor_explanation(
                                    cur=cur,
                                    student_id=student_id,
                                    concept_id=int(tutor_concept_id),
                                    concept_name=str(tutor_concept_name),
                                    misconception=misconception,
                                    explanation_style=explanation_style,
                                    attempt_count=attempt_count,
                                    year_level=year_level,
                                )
            except Exception as tutor_exc:
                logger.warning("student_chat tutor augmentation failed: %s", tutor_exc)
                tutor_explanation = None
                tutor_cache_hit = False

        return {
            "response": ai_reply,
            "conversation_id": conversation_id,
            "lightbulb_detected": False,
            "tutor_explanation": tutor_explanation,
            "cache_hit": tutor_cache_hit,
        }
    except Exception as e:
        logger.exception("student_chat failed: %s", e)
        return fallback


@app.post("/tutor/explain")
def tutor_explain(body: dict):
    try:
        required_fields = ["student_id", "concept_id", "concept_name", "explanation_style", "attempt_count"]
        for field_name in required_fields:
            if field_name not in body or body[field_name] is None:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field_name}")

        try:
            student_id = int(body["student_id"])
            concept_id = int(body["concept_id"])
            concept_name = str(body["concept_name"]).strip()
            explanation_style = str(body["explanation_style"]).strip()
            attempt_count = int(body["attempt_count"])
            year_level_raw = body.get("year_level", 10)
            year_level = int(year_level_raw) if year_level_raw is not None else 10
            misconception_raw = body.get("misconception")
            misconception = str(misconception_raw).strip() if misconception_raw is not None else None
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid field type in request body")

        if not concept_name:
            raise HTTPException(status_code=400, detail="Missing required field: concept_name")

        if explanation_style not in VALID_EXPLANATION_STYLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid explanation_style. Valid styles: {', '.join(sorted(list(VALID_EXPLANATION_STYLES)))}",
            )

        with get_db() as cur:
            cur.execute("SELECT id FROM students WHERE id = %s", (student_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Student not found")

            try:
                explanation, cache_hit, _model_used = generate_tutor_explanation(
                    cur=cur,
                    student_id=student_id,
                    concept_id=concept_id,
                    concept_name=concept_name,
                    misconception=misconception,
                    explanation_style=explanation_style,
                    attempt_count=attempt_count,
                    year_level=year_level,
                )
            except RuntimeError as e:
                if "OPENAI_API_KEY" in str(e):
                    raise HTTPException(
                        status_code=503,
                        detail="AI tutor not configured — contact admin to add OPENAI_API_KEY",
                    )
                raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                raise HTTPException(status_code=502, detail=f"OpenAI API error: {e.code} {body}")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")

        return {
            "explanation": explanation,
            "style": explanation_style,
            "cache_hit": cache_hit,
            "concept_name": concept_name,
            "attempt_count": attempt_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MasteryPredictionRequest(BaseModel):
    student_id: int
    concept_id: int

@app.post("/predict/mastery")
def predict_mastery(req: MasteryPredictionRequest):
    models = get_models()
    if "concept_mastery" not in models:
        raise HTTPException(503, "Mastery model not loaded")

    model_data = models["concept_mastery"]
    encoders = models.get("encoders", {})

    with get_db() as cur:
        features = _build_mastery_features(cur, req.student_id, req.concept_id, encoders)

    if not features:
        raise HTTPException(404, "Student/concept not found")

    import pandas as pd
    X = pd.DataFrame([features])[model_data["features"]]
    pred = model_data["model"].predict(X)[0]

    return {
        "student_id": req.student_id,
        "concept_id": req.concept_id,
        "predicted_mastery": round(float(pred), 4),
        "model_r2": model_data.get("test_r2", "N/A"),
    }


# =============================================================================
# FEATURE BUILDERS FOR LIVE PREDICTIONS
# =============================================================================

def _build_student_features(cur, student_id, encoders):
    cur.execute("""
        SELECT s.year_level, s.gender,
               p.dominant_learning_style, p.best_time_of_day,
               p.average_response_time_seconds, p.frustration_threshold,
               p.prefers_short_explanations, p.prefers_encouragement,
               p.average_session_length_minutes, p.total_interactions,
               p.overall_mastery_trend, p.overall_engagement_score, p.overall_risk_score,
               w.has_learning_support_plan, w.has_medical_condition,
               w.home_situation_flag, w.is_esol, w.attendance_percentage
        FROM students s
        LEFT JOIN student_learning_profiles p ON p.student_id = s.id
        LEFT JOIN student_wellbeing_context w ON w.student_id = s.id
        WHERE s.id = %s
    """, (student_id,))
    row = cur.fetchone()
    if not row:
        return None

    f = dict(row)

    # Encode categoricals
    try:
        f["gender_enc"] = encoders["gender"].transform([f.get("gender","Male")])[0]
        f["learning_style_enc"] = encoders["learning_style"].transform([f.get("dominant_learning_style","visual")])[0]
        f["time_of_day_enc"] = encoders["time_of_day"].transform([f.get("best_time_of_day","morning")])[0]
        f["trend_enc"] = encoders["trend"].transform([f.get("overall_mastery_trend","stable")])[0]
    except:
        f["gender_enc"] = 0
        f["learning_style_enc"] = 0
        f["time_of_day_enc"] = 0
        f["trend_enc"] = 0

    # Conversation aggregates
    cur.execute("""
        SELECT COUNT(*) as total_conversations,
               COALESCE(AVG(session_engagement_score),0) as avg_engagement,
               COALESCE(SUM(CASE WHEN lightbulb_moment_detected THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*),0),0) as lightbulb_rate,
               COALESCE(SUM(CASE WHEN outcome='resolved' THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*),0),0) as resolve_rate,
               COALESCE(SUM(CASE WHEN outcome='abandoned' THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*),0),0) as abandon_rate,
               COALESCE(AVG(total_messages),0) as avg_conv_messages,
               COALESCE(AVG(EXTRACT(EPOCH FROM (ended_at-started_at))/60),0) as avg_duration
        FROM conversations WHERE student_id = %s
    """, (student_id,))
    f.update(cur.fetchone())

    # Message aggregates
    cur.execute("""
        SELECT COALESCE(AVG(response_time_seconds),0) as avg_response_time,
               COALESCE(SUM(CASE WHEN frustration_signal THEN 1 ELSE 0 END)::float /
               NULLIF(SUM(CASE WHEN sender='student' THEN 1 ELSE 0 END),0),0) as frustration_rate,
               COALESCE(AVG(word_count),0) as avg_word_count
        FROM messages WHERE student_id = %s
    """, (student_id,))
    f.update(cur.fetchone())

    # Quiz aggregates
    cur.execute("""
        SELECT COALESCE(COUNT(*),0) as total_quizzes,
               COALESCE(AVG(score_percentage),0) as avg_quiz_score,
               COALESCE(MIN(score_percentage),0) as min_quiz_score,
               COALESCE(STDDEV(score_percentage),0) as quiz_score_std
        FROM quiz_sessions WHERE student_id = %s
    """, (student_id,))
    f.update(cur.fetchone())

    # Mastery aggregates
    cur.execute("""
        SELECT COALESCE(AVG(mastery_score),0) as avg_mastery,
               COALESCE(MIN(mastery_score),0) as min_mastery,
               COALESCE(AVG(confidence),0) as avg_confidence,
               COALESCE(AVG(evidence_count),0) as avg_evidence
        FROM concept_mastery_states WHERE student_id = %s
    """, (student_id,))
    f.update(cur.fetchone())

    return {k: (v if v is not None else 0) for k, v in f.items()}


def _build_mastery_features(cur, student_id, concept_id, encoders):
    cur.execute("SELECT difficulty_level, year_level_introduced, concept_type FROM concepts WHERE id = %s", (concept_id,))
    concept = cur.fetchone()
    if not concept:
        return None

    cur.execute("""
        SELECT average_response_time_seconds, frustration_threshold,
               overall_engagement_score, overall_risk_score, total_interactions
        FROM student_learning_profiles WHERE student_id = %s
    """, (student_id,))
    profile = cur.fetchone()
    if not profile:
        return None

    cur.execute("""
        SELECT confidence, evidence_count, last_quiz_score, last_conversation_outcome, trend
        FROM concept_mastery_states WHERE student_id = %s AND concept_id = %s
    """, (student_id, concept_id))
    mastery = cur.fetchone()

    cur.execute("""
        SELECT COALESCE(COUNT(*),0) as concept_convos,
               COALESCE(AVG(session_engagement_score),0) as concept_engagement,
               COALESCE(SUM(CASE WHEN lightbulb_moment_detected THEN 1 ELSE 0 END),0) as concept_lightbulbs
        FROM conversations WHERE student_id = %s AND concept_id = %s
    """, (student_id, concept_id))
    conv_stats = cur.fetchone()

    cur.execute("""
        SELECT COALESCE(AVG(score_percentage),0) as concept_quiz_avg,
               COALESCE(COUNT(*),0) as concept_quiz_count
        FROM quiz_sessions WHERE student_id = %s AND concept_id = %s
    """, (student_id, concept_id))
    quiz_stats = cur.fetchone()

    from sklearn.preprocessing import LabelEncoder
    outcome_enc = LabelEncoder()
    outcome_enc.fit(["abandoned","partially_resolved","resolved","unresolved"])
    trend_enc = LabelEncoder()
    trend_enc.fit(["declining","improving","stable"])
    ctype_enc = LabelEncoder()
    ctype_enc.fit(["applied","conceptual","foundational","procedural"])

    f = {
        "difficulty_level": concept["difficulty_level"] or 5,
        "year_level_introduced": concept["year_level_introduced"] or 10,
        "concept_type_enc": ctype_enc.transform([concept["concept_type"] or "conceptual"])[0],
        "confidence": mastery["confidence"] if mastery else 0.5,
        "evidence_count": mastery["evidence_count"] if mastery else 0,
        "last_quiz_score": mastery["last_quiz_score"] if mastery else 0.5,
        "outcome_enc": outcome_enc.transform([mastery["last_conversation_outcome"] or "unresolved"])[0] if mastery else 0,
        "trend_enc": trend_enc.transform([mastery["trend"] or "stable"])[0] if mastery else 0,
        "average_response_time_seconds": profile["average_response_time_seconds"] or 20,
        "frustration_threshold": profile["frustration_threshold"] or 0.5,
        "overall_engagement_score": profile["overall_engagement_score"] or 0.5,
        "overall_risk_score": profile["overall_risk_score"] or 0.3,
        "total_interactions": profile["total_interactions"] or 0,
        "concept_convos": conv_stats["concept_convos"],
        "concept_engagement": conv_stats["concept_engagement"],
        "concept_lightbulbs": conv_stats["concept_lightbulbs"],
        "concept_quiz_avg": quiz_stats["concept_quiz_avg"],
        "concept_quiz_count": quiz_stats["concept_quiz_count"],
    }

    return {k: (v if v is not None else 0) for k, v in f.items()}


# =============================================================================
# HELPERS
# =============================================================================

def _clean(row):
    """Convert RealDictRow to JSON-safe dict."""
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
        elif isinstance(v, (bytes, memoryview)):
            d[k] = str(v)
        elif hasattr(v, 'item'):  # numpy types
            d[k] = v.item()
    return d


# =============================================================================
# LAMBDA HANDLER
# =============================================================================

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    pass


# =============================================================================
# LOCAL DEV
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AxonAI API on http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)