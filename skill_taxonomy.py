"""
Canonical skill taxonomy and misconception tags for AxonAI.
Use these identifiers consistently across all endpoints.
"""

SKILL_TAXONOMY = {
    'math': ['algebra', 'geometry', 'arithmetic', 'statistics', 'functions', 'calculus', 'general'],
    'english': ['grammar', 'writing', 'reading_comprehension', 'vocabulary', 'literature', 'general'],
    'science': ['biology', 'chemistry', 'physics', 'earth_science', 'scientific_method', 'general'],
    'history': ['ancient', 'medieval', 'modern', 'civics', 'geography', 'source_analysis', 'general']
}

MISCONCEPTION_TAGS = {
    'math': [
        'sign_error', 'order_of_operations', 'variable_confusion', 'fraction_operations',
        'equation_balance', 'distribution_error', 'unit_mismatch', 'geometry_formula_confusion'
    ],
    'english': [
        'tense_agreement', 'subject_verb_agreement', 'punctuation_error', 'unclear_thesis',
        'weak_evidence', 'misreading_prompt', 'quotation_integration', 'vocabulary_misuse'
    ],
    'science': [
        'cause_vs_correlation', 'unit_conversion', 'variable_control', 'misconception_energy',
        'misconception_forces', 'misunderstanding_cells', 'misunderstanding_reactions', 'graph_interpretation'
    ],
    'history': [
        'chronology_confusion', 'causation_oversimplified', 'source_bias_missed', 'context_missing',
        'terminology_confusion', 'evidence_claim_mismatch', 'perspective_missing'
    ]
}

TEACHING_STRATEGIES = [
    'step_by_step',
    'worked_example',
    'socratic',
    'scaffolding',
    'analogy',
    'visual',
    'chunking',
    'spaced_retrieval',
    'elaboration',
    'quick_check'
]

DEFAULT_STRATEGIES = {
    'math': 'step_by_step',
    'science': 'step_by_step',
    'english': 'worked_example',
    'history': 'worked_example'
}

EPSILON = 0.15

QUICK_CHECK_WEIGHT = 1.0
QUIZ_WEIGHT = 1.5
SUCCESS_THRESHOLD = 0.70

def get_subject_skills(subject):
    """Get valid skills for a subject."""
    subject = subject.lower()
    subject_aliases = {'mathematics': 'math', 'maths': 'math'}
    subject = subject_aliases.get(subject, subject)
    return SKILL_TAXONOMY.get(subject, ['general'])

def get_subject_misconceptions(subject):
    """Get valid misconception tags for a subject."""
    subject = subject.lower()
    subject_aliases = {'mathematics': 'math', 'maths': 'math'}
    subject = subject_aliases.get(subject, subject)
    return MISCONCEPTION_TAGS.get(subject, [])

def get_default_strategy(subject):
    """Get default cold-start strategy for a subject."""
    subject = subject.lower()
    subject_aliases = {'mathematics': 'math', 'maths': 'math'}
    subject = subject_aliases.get(subject, subject)
    return DEFAULT_STRATEGIES.get(subject, 'step_by_step')

def normalize_subject(subject):
    """Normalize subject name."""
    if not subject:
        return 'general'
    subject = subject.lower()
    subject_aliases = {'mathematics': 'math', 'maths': 'math'}
    return subject_aliases.get(subject, subject)
