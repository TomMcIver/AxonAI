# AxonAI Demo Data Simulator Guide

## Overview

The simulator generates realistic demo cohorts with students, interactions, assessments, and learning outcomes. Use it to populate the database with data for demos and testing.

## Quick Start

```bash
# Generate 100 students, 30 days of data, 3 classes
python scripts/simulate_school.py --students 100 --days 30 --classes 3 --seed 42

# Generate larger cohort for demo
python scripts/simulate_school.py --students 500 --days 60 --classes 6 --seed 123

# Generate very large cohort
python scripts/simulate_school.py --students 5000 --days 90 --classes 20 --seed 456
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--students` | 100 | Number of students to generate |
| `--days` | 30 | Days of historical data |
| `--classes` | 3 | Number of classes |
| `--seed` | 42 | Random seed for reproducibility |
| `--subject` | math | Subject area (math, science, english, history) |
| `--teacher-id` | None | Teacher user ID (auto-creates if not provided) |
| `--dry-run` | False | Generate without saving to database |
| `--output` | None | Output JSON file for dry run |

## Generated Data

### Students

Each student has:

**Profile Data**:
- Name, age, gender, ethnicity
- Year level (9-13)
- Learning style (visual, auditory, kinesthetic, reading)
- Learning difficulty (optional: Dyslexia, ADHD, etc.)
- Extracurricular activities
- Academic goals

**Latent Traits** (hidden, drive behavior):
- `baseline_ability`: 0.2 - 0.95 (normal distribution, μ=0.6)
- `learning_rate`: 0.01 - 0.15 (how fast they learn)
- `engagement_tendency`: 0.2 - 0.95 (how engaged they are)
- `consistency`: 0.3 - 0.95 (how stable their performance is)
- `help_seeking`: 0.1 - 0.9 (how often they ask for help)
- `skill_strengths`: 1-2 skills with +10-25% bonus
- `skill_weaknesses`: 1-2 skills with -10-25% penalty
- `strategy_sensitivities`: Per-strategy effectiveness modifiers

### Interactions

**Realistic patterns**:
- Session-based interactions (3-8 per session)
- Time-of-day variation
- Strategy-dependent success rates
- Engagement scores based on latent traits
- Response time variation

**Message templates**:
- Initial questions about topics
- Correct understanding responses
- Confused/help-seeking responses
- Follow-up questions

### Quizzes

- Multiple skills tested per quiz
- Score based on latent ability + skill modifiers
- Realistic time-taken values
- Per-skill score breakdown

### Learning Patterns

The simulator generates three types of learning curves:

1. **Improvement** (60%): Gradual increase in mastery
2. **Plateau** (20%): Improvement followed by stagnation
3. **Regression** (20%): Initial improvement then decline

## Example Outputs

### Small Demo (100 students)

```bash
python scripts/simulate_school.py --students 100 --days 30 --classes 3

Generated:
  - 100 students
  - 3 classes
  - ~2,500 interactions
  - ~60 quizzes
  - ~400 mastery states
```

### Medium Demo (500 students)

```bash
python scripts/simulate_school.py --students 500 --days 60 --classes 6

Generated:
  - 500 students
  - 6 classes
  - ~15,000 interactions
  - ~300 quizzes
  - ~2,000 mastery states
```

### Large Demo (5000 students)

```bash
python scripts/simulate_school.py --students 5000 --days 90 --classes 20

Generated:
  - 5,000 students
  - 20 classes
  - ~180,000 interactions
  - ~3,000 quizzes
  - ~20,000 mastery states
```

## Dry Run Mode

Preview generated data without affecting the database:

```bash
# Preview only
python scripts/simulate_school.py --students 50 --dry-run

# Save to JSON file
python scripts/simulate_school.py --students 50 --dry-run --output demo_data.json
```

## Post-Generation Steps

After generating data, train the ML models:

```bash
# 1. Train mastery model
python training/train_mastery.py

# 2. Train risk model
python training/train_risk.py

# 3. Evaluate all models
python training/evaluate.py
```

## Reproducibility

Use the `--seed` flag to generate identical data:

```bash
# These will produce identical results
python scripts/simulate_school.py --students 100 --seed 42
python scripts/simulate_school.py --students 100 --seed 42
```

## Customization

### Adding New Subjects

Edit `skill_taxonomy.py` to add skills:

```python
SKILL_TAXONOMY = {
    'math': ['algebra', 'geometry', ...],
    'new_subject': ['skill1', 'skill2', ...]
}
```

### Modifying Student Traits

Edit `simulator/student_generator.py`:

```python
def generate_latent_traits(self) -> Dict:
    # Adjust distributions here
    baseline_ability = np.clip(np.random.normal(0.6, 0.15), 0.2, 0.95)
    ...
```

### Changing Interaction Patterns

Edit `simulator/interaction_simulator.py`:

```python
QUESTION_TEMPLATES = {
    'math': [
        # Add new templates here
    ]
}
```

## Database Tables Populated

| Table | Description |
|-------|-------------|
| `user` | Student profiles |
| `class` | Class definitions |
| `class_users` | Student-class associations |
| `ai_interaction` | Tutor conversations |
| `optimized_profile` | Student optimization data |
| `mastery_state` | Per-skill mastery levels |

## Troubleshooting

### "No teacher found" Error

Create a teacher first:
```bash
python scripts/simulate_school.py --teacher-id 1
```

### Database Errors

Reset the database:
```python
from app import db, app
with app.app_context():
    db.drop_all()
    db.create_all()
```

### Memory Issues with Large Cohorts

Generate in batches:
```bash
python scripts/simulate_school.py --students 1000 --classes 5 --seed 1
python scripts/simulate_school.py --students 1000 --classes 5 --seed 2
```
