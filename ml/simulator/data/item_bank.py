"""ItemBank carrying calibrated 2PL (a, b) and Eedi 2024 distractor metadata.

Implemented in PR 6.

Planned shape:
    Item: item_id, concept_id, a, b, distractors: list[Distractor]
    Distractor: option_text, misconception_id | None  (populated where Eedi matches)

v1 response model ignores misconception_id.
"""
