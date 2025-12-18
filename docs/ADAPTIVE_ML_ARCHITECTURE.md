# AxonAI Adaptive ML Architecture

## Overview

AxonAI uses machine learning to provide personalized, adaptive tutoring. This document describes the ML architecture, data flows, and model versioning.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AxonAI ML Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Student   │───▶│  AI Tutor   │───▶│  Mastery    │          │
│  │ Interaction │    │   Service   │    │   Model     │          │
│  └─────────────┘    └─────────────┘    └──────┬──────┘          │
│                            │                   │                  │
│                            ▼                   ▼                  │
│                     ┌─────────────┐    ┌─────────────┐          │
│                     │  Contextual │    │    Risk     │          │
│                     │   Bandit    │    │   Model     │          │
│                     └──────┬──────┘    └──────┬──────┘          │
│                            │                   │                  │
│                            ▼                   ▼                  │
│                     ┌─────────────────────────────┐              │
│                     │    Teacher Dashboard        │              │
│                     │  - Risk Alerts              │              │
│                     │  - Mastery Heatmaps         │              │
│                     │  - Strategy Analytics       │              │
│                     └─────────────────────────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Mastery Model (`mastery_model/`)

**Purpose**: Predict P(mastered) for each (student, skill) pair.

**Features** (18 dimensions):
- Attempt count and correctness history
- Rolling accuracy (5 and 10 attempts)
- Average difficulty and time taken
- Hint usage rate
- Engagement score average
- Session count and recency
- Streak metrics (current and max)
- Improvement trend and consistency

**Model**: Logistic Regression with isotonic calibration

**Storage**:
- Model artifacts: `models/mastery/<version>/model.pkl`
- State table: `MasteryState(student_id, skill, p_mastery, confidence, ...)`

### 2. Risk Model (`risk_model/`)

**Purpose**: Predict P(at_risk_next_14_days) for each student.

**Features** (20 dimensions):
- Mastery slope (7-day and 14-day)
- Average and minimum mastery
- Engagement trend and current level
- Missed attempts rate
- Low accuracy streak
- Attendance rate
- Days since activity
- Topic churn rate
- Quiz score average and trend
- Negative indicator rate
- Help request rate
- Difficulty mismatch

**Model**: Logistic Regression with balanced class weights

**Explanations**: Top-5 feature contributions using coefficient analysis

**Storage**:
- Model artifacts: `models/risk/<version>/model.pkl`
- State table: `RiskScore(student_id, class_id, p_risk, top_drivers_json, ...)`

### 3. Contextual Bandit (`bandit/`)

**Purpose**: Select optimal teaching strategy based on student context.

**Strategies** (10 arms):
1. step_by_step
2. worked_example
3. socratic
4. scaffolding
5. analogy
6. visual
7. chunking
8. spaced_retrieval
9. elaboration
10. quick_check

**Context Vector** (10 dimensions):
- Current mastery level
- Risk level
- Engagement score
- Difficulty preference
- Time of day
- Session length
- Recent accuracy
- Streak length
- Topic familiarity
- Help request rate

**Algorithm**: LinUCB with α=1.0 exploration parameter

**Reward Signal**:
- Primary (60%): Mastery gain Δp_mastery
- Secondary (25%): Correctness of next attempt
- Tertiary (15%): Engagement change

**Storage**:
- State table: `BanditPolicyState(student_id, class_id, policy_state_json, ...)`

### 4. Embedding Retrieval (`retrieval/`)

**Purpose**: Semantic content retrieval for RAG.

**Embedding Model**: OpenAI text-embedding-3-small (1536d) or TF-IDF fallback (500d)

**Chunking**: 500 words with 50-word overlap

**Storage**:
- Table: `ContentEmbedding(class_id, content_file_id, chunk_text, embedding_json, ...)`

## Data Flow

### 1. Interaction Flow

```
Student Message
     │
     ▼
┌─────────────────┐
│ Retrieve Content│ (Embedding similarity)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Context     │ (Mastery, Risk, Profile)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select Strategy │ (LinUCB bandit)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Response│ (GPT with context)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update States   │ (Mastery, Bandit)
└─────────────────┘
```

### 2. Assessment Flow

```
Quiz Submission
     │
     ▼
┌─────────────────┐
│ Score Quiz      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Mastery  │ (Per skill)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Risk     │ (Recalculate)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Bandit   │ (Reward signal)
└─────────────────┘
```

## Model Versioning

### Version Format

`v{YYYYMMDD}_{HHMMSS}`

Example: `v20241218_143052`

### Version Storage

```
models/
├── mastery/
│   ├── v20241218_143052/
│   │   ├── model.pkl
│   │   └── metrics.json
│   └── v20241217_091234/
│       ├── model.pkl
│       └── metrics.json
└── risk/
    └── v20241218_143052/
        ├── model.pkl
        └── metrics.json
```

### Database Tracking

```sql
CREATE TABLE model_version (
    id INTEGER PRIMARY KEY,
    model_type VARCHAR(50),  -- 'mastery', 'risk'
    version VARCHAR(100),
    metrics_json TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMP
);
```

## Training Pipeline

### Scheduled Training

```bash
# Daily retrain (or every N interactions)
python training/roll_forward_retrain.py

# Manual training
python training/train_mastery.py
python training/train_risk.py

# Evaluation
python training/evaluate.py
```

### Metrics Logged

**Mastery Model**:
- Accuracy, AUC-ROC, Log Loss
- Calibration Error (ECE)
- Feature Importance

**Risk Model**:
- Accuracy, Precision, Recall, F1
- AUC-ROC
- Per-feature importance

## Feature Flags

```python
# In services/ml_integration.py
USE_ML_MASTERY = True          # Use ML mastery vs heuristics
USE_ML_RISK = True             # Use ML risk vs thresholds
USE_CONTEXTUAL_BANDIT = True   # Use LinUCB vs epsilon-greedy
USE_EMBEDDING_RETRIEVAL = True # Use embeddings vs keywords
```

## Fallback Behavior

When ML models are unavailable:

1. **Mastery**: Falls back to heuristic based on rolling accuracy
2. **Risk**: Falls back to threshold-based rules (grade < 60%)
3. **Bandit**: Falls back to epsilon-greedy with ε=0.15
4. **Retrieval**: Falls back to keyword overlap scoring

## Performance Considerations

- **Batch predictions**: Use `batch_predict()` for multiple students
- **Caching**: Vector stores cached per class
- **Incremental updates**: Mastery and bandit support online learning
- **Model size**: ~100KB per model artifact

## Monitoring

Check model health:

```python
from training.evaluate import evaluate_all_models
results = evaluate_all_models()
```

View retrain history:

```bash
cat models/retrain_log.json
```
