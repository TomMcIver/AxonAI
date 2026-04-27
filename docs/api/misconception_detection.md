# Misconception Detection on Quiz Submission

## Endpoint

- `POST /quiz/submit`

## When detection runs

- Detection runs only when a submitted answer is incorrect (`is_correct = false`).
- Correct answers skip misconception detection entirely.

## Detection inputs

When an answer is wrong, the API builds detector input from:

- `question_text` from `quiz_questions`
- the student's submitted wrong `student_answer`
- `concept_name` from `concepts`

The route calls the adapter:

- `detect_misconception(question_text, wrong_answer, concept_name)`

If the detector throws (import or runtime), the API logs a warning and continues.
Quiz submission does not fail due to detector errors.

## Confidence threshold

- Only the top detected misconception with confidence greater than `0.5` is accepted.
- If confidence is `<= 0.5` (or no result), no misconception flag is written.

## Database writes

On every submission, `quiz_questions` is updated with:

- `student_answer`
- `is_correct`
- `time_taken_seconds`

On wrong answers with accepted detector confidence:

- `student_concept_flags` is written with:
  - `student_id`
  - `concept_id`
  - `flag_type = 'misconception'`
  - `flag_detail = <detected misconception text>`
  - `root_cause_concept_id = concept_id`
  - `raised_at = now()`
  - `is_active = true`
  - `recommended_intervention = null`

Duplicate behavior:

- If an active matching flag already exists for the same student + concept + misconception text, no new row is inserted.
- Existing row `raised_at` is updated instead.

## Response fields

The endpoint returns:

- `is_correct`
- `correct_answer`
- `detected_misconception` (string or `null`)
- `misconception_confidence` (float or `null`)

