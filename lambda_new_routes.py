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

NOTE: Responses are intentionally flat (no nested wrapper keys) so the
React frontend can access fields directly on the parsed JSON object.
"""


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
