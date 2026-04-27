# Student Data Deletion Endpoint

## Endpoint

- Method: `DELETE`
- Path: `/students/{student_id}/data`

## Purpose

This endpoint permanently deletes a student's data across the platform to support privacy deletion requests under the NZ Privacy Act 2020.

## Request Body

```json
{
  "confirm_delete": true
}
```

- `confirm_delete` is required and must be `true`.
- If not present or not `true`, API returns `400` with:
  - `"Set confirm_delete to true to proceed. This action is permanent and cannot be undone."`

## Deletion Behavior

The deletion runs in a single transaction. If any delete fails, the whole operation is rolled back.

Delete order:
1. `student_concept_flags`
2. `student_learning_profiles`
3. `messages`
4. `conversations`
5. `quiz_questions` (linked by `student_id` or by student conversations)
6. `teacher_ai_insights` (if table and `student_id` exist)
7. `pedagogical_memory` (if table and `student_id` exist)
8. `grade` (if table and `student_id` exist)
9. `students` (final delete)

Tables that do not exist are skipped silently.

## Logging

Each successful deletion inserts one row into `data_deletion_log`:
- `id`
- `student_id`
- `deleted_at`
- `deleted_by` (`"api_request"`)
- `rows_deleted` (JSON object of table name to deleted row count)

## Responses

- `200 OK`: deletion completed with `student_id`, `deleted_at`, `rows_deleted`, and confirmation message.
- `404 Not Found`: student does not exist.
- `400 Bad Request`: confirmation missing or false.
- `500 Internal Server Error`: deletion failure (no partial deletion due to transaction rollback).

## Recommended Parent Request Process

1. Receive and verify parent/student deletion request.
2. Call `DELETE /students/{student_id}/data` with `{"confirm_delete": true}`.
3. Confirm completion using `data_deletion_log`.
4. Notify parent/student of completion within 20 working days under NZ Privacy Act 2020.
