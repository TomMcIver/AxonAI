# `/tutor/explain` API

## Overview

`POST /tutor/explain` returns an AI-generated explanation tailored to a student's misconception.

Responses are cached in `messages` rows with:
- `sender = 'ai_tutor'`
- `cache_key = md5(concept_id, misconception, explanation_style)`
- `is_cached = true`
- `model_used = 'claude-haiku-4-5'`

## Request Body

```json
{
  "student_id": 1,
  "concept_id": 5,
  "concept_name": "fractions",
  "misconception": "believes you add denominators when adding fractions",
  "explanation_style": "contrast_with_misconception",
  "attempt_count": 3,
  "year_level": 10
}
```

### Fields

- `student_id` (int, required)
- `concept_id` (int, required)
- `concept_name` (string, required)
- `misconception` (string, optional; if omitted/null, a general explanation is generated)
- `explanation_style` (string, required)
- `attempt_count` (int, required)
- `year_level` (int, optional, defaults to `10`)

### Valid `explanation_style` values

- `worked_example`
- `socratic`
- `contrast_with_misconception`
- `analogy`
- `decompose_to_prerequisites`

## Response Body

```json
{
  "explanation": "When adding fractions, the denominator tells you the size of each piece, so those sizes must match before you add.",
  "style": "contrast_with_misconception",
  "cache_hit": false,
  "concept_name": "fractions",
  "attempt_count": 3
}
```

## Cache Behavior

1. Cache key is built from `(concept_id, misconception, explanation_style)` and hashed with MD5.
2. Endpoint checks `messages` for:
   - `sender = 'ai_tutor'`
   - matching `cache_key`
   - `is_cached = true`
3. On match:
   - returns cached `content`
   - sets `cache_hit = true`
   - does not call Anthropic.
4. On miss:
   - builds prompt from style template
   - calls Anthropic (`claude-haiku-4-5`, max `300` tokens)
   - writes response to `messages` with cache metadata
   - returns `cache_hit = false`.

## Error Codes

- `400` Missing required field (returns field name)
- `400` Invalid `explanation_style` (returns valid style list)
- `404` Student not found
- `503` AI tutor not configured:
  - `"AI tutor not configured — contact admin to add ANTHROPIC_API_KEY"`
- `502` Anthropic API call failed
- `500` All other unexpected server errors

## Required Environment Configuration

This endpoint reads `ANTHROPIC_API_KEY` from Lambda environment variables.

If missing, `/tutor/explain` returns `503` and does not crash.

### Setup steps (AWS Console)

1. AWS Console -> Lambda
2. Open function: `axonai-api`
3. Go to **Configuration**
4. Go to **Environment variables**
5. Click **Add environment variable**
6. Key: `ANTHROPIC_API_KEY`
7. Value: paste the Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
