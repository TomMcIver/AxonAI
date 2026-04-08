"""
New Lambda FastAPI routes for AxonAI teacher dashboard.

ADD THESE ROUTES to your existing Lambda FastAPI app (axonai_api.py or equivalent)
then redeploy the Lambda function.

Deployment:
    zip -r lambda_package.zip .
    aws lambda update-function-code \
        --function-name axonai-api \
        --zip-file fileb://lambda_package.zip \
        --region ap-southeast-2

These routes serve data from:
  - teacher_ai_insights        → /student/{id}/ai-insights
  - student_wellbeing_context  → /student/{id}/wellbeing
  - pedagogical_memory         → /student/{id}/pedagogical-memory
  - concepts + prerequisites   → /concepts/{subject}
  - class concept mastery      → /class/{id}/concept-summary

NOTE: Responses are intentionally flat (no nested wrapper keys) so the
React frontend can access fields directly on the parsed JSON object.
"""


@app.get("/concepts/{subject}")
def get_concepts(subject: str):
    """All concepts for a subject with prerequisite relationships.

    Returns concept list including question_count per concept so the
    frontend Knowledge Graph can display question availability badges.
    """
    with get_db() as cur:
        cur.execute(
            """
            SELECT c.id, c.name, c.difficulty_level, c.concept_type,
                   COUNT(qq.id) AS question_count
            FROM concepts c
            LEFT JOIN quiz_questions qq ON qq.concept_id = c.id
            WHERE c.subject_id = (SELECT id FROM subjects WHERE name = %s LIMIT 1)
            GROUP BY c.id, c.name, c.difficulty_level, c.concept_type
            ORDER BY c.id
            """,
            (subject,),
        )
        concepts = [
            {
                "id": r[0],
                "name": r[1],
                "difficulty_level": r[2],
                "concept_type": r[3],
                "question_count": r[4],
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT cp.concept_id, cp.prerequisite_concept_id, cp.strength
            FROM concept_prerequisites cp
            WHERE cp.concept_id IN (
                SELECT id FROM concepts
                WHERE subject_id = (SELECT id FROM subjects WHERE name = %s LIMIT 1)
            )
            """,
            (subject,),
        )
        prerequisites = [
            {
                "concept_id": r[0],
                "prerequisite_concept_id": r[1],
                "strength": r[2],
            }
            for r in cur.fetchall()
        ]

        return {"concepts": concepts, "prerequisites": prerequisites}


@app.get("/class/{class_id}/concept-summary")
def get_class_concept_summary(class_id: int):
    """Concept mastery summary for a class (top 20 by average mastery).

    Used by the Teacher Dashboard "Class Concept Strengths" widget.
    avg_mastery is a float 0.0–1.0.
    """
    with get_db() as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.name,
                AVG(CAST(cms.mastery_score AS FLOAT)) / 100.0 AS avg_mastery,
                COUNT(CASE WHEN cms.mastery_score >= 80 THEN 1 END) AS students_mastered,
                COUNT(CASE WHEN cms.mastery_score < 50 THEN 1 END) AS students_struggling,
                COUNT(qq.id) AS question_count
            FROM concepts c
            LEFT JOIN concept_mastery_states cms ON c.id = cms.concept_id
            LEFT JOIN quiz_questions qq ON qq.concept_id = c.id
            WHERE cms.class_id = %s
            GROUP BY c.id, c.name
            ORDER BY avg_mastery DESC
            LIMIT 20
            """,
            (class_id,),
        )
        return {
            "concepts": [
                {
                    "concept_id": r[0],
                    "name": r[1],
                    "avg_mastery": r[2],
                    "students_mastered": r[3],
                    "students_struggling": r[4],
                    "question_count": r[5],
                }
                for r in cur.fetchall()
            ]
        }


@app.get("/student/{student_id}/ai-insights")
def get_ai_insights(student_id: int):
    """GPT-4o generated teacher insights for a student."""
    with get_db() as cur:
        cur.execute(
            """
            SELECT student_summary, risk_narrative,
                   recommended_interventions, teaching_approach_advice,
                   generated_at, model_used
            FROM teacher_ai_insights
            WHERE student_id = %s AND class_id = 1
            ORDER BY generated_at DESC LIMIT 1
            """,
            (student_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "student_summary": row[0],
            "risk_narrative": row[1],
            "recommended_interventions": row[2],
            "teaching_approach_advice": row[3],
            "generated_at": row[4].isoformat() if row[4] else None,
            "model_used": row[5],
        }


@app.get("/student/{student_id}/wellbeing")
def get_wellbeing(student_id: int):
    """Wellbeing context for a student (IEP, ESOL, pastoral flags, attendance)."""
    with get_db() as cur:
        cur.execute(
            """
            SELECT has_learning_support_plan, learning_support_details,
                   has_medical_condition, medical_details,
                   home_situation_flag, home_situation_notes,
                   is_esol, attendance_percentage
            FROM student_wellbeing_context
            WHERE student_id = %s
            """,
            (student_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "has_learning_support_plan": row[0],
            "learning_support_details": row[1],
            "has_medical_condition": row[2],
            "medical_details": row[3],
            "home_situation_flag": row[4],
            "home_situation_notes": row[5],
            "is_esol": row[6],
            "attendance_percentage": row[7],
        }


@app.get("/student/{student_id}/pedagogical-memory")
def get_pedagogical_memory(student_id: int):
    """Teaching approaches and their success rates for a student."""
    with get_db() as cur:
        cur.execute(
            """
            SELECT teaching_approach, success_rate, attempt_count,
                   avg_messages_to_lightbulb, last_used_at
            FROM pedagogical_memory
            WHERE student_id = %s
            ORDER BY success_rate DESC
            """,
            (student_id,),
        )
        rows = cur.fetchall()
        return {
            "approaches": [
                {
                    "teaching_approach": r[0],
                    "success_rate": r[1],
                    "attempt_count": r[2],
                    "avg_messages_to_lightbulb": r[3],
                    "last_used_at": r[4].isoformat() if r[4] else None,
                }
                for r in rows
            ]
        }
