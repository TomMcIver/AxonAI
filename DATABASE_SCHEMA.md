# 📊 AxonAI Database Architecture & Schema

**Complete reference** for the learning intelligence platform powering cognitive infrastructure in New Zealand secondary schools (Years 7–13, NCEA curriculum).

---

## 🎯 Overview

AxonAI's database is not a traditional LMS. It's **cognitive infrastructure** where every student interaction feeds pedagogical memory, which drives better tutoring strategies, which generates teacher insights. The feedback loops are tight, data is rich, and intelligence is actionable.

**Core Positioning**: Augment teachers through AI-generated insights, adaptive Socratic tutoring, and predictive risk models — not replace them.

---

## 🏗️ System Architecture (4 Layers)

### Layer 1: Foundation — Users & Classes
Identity, enrollment, basic course structure

### Layer 2: Learning Intelligence — Pedagogical Memory & Caching
What works for each student, what doesn't, real-time performance cache

### Layer 3: AI Interactions — Conversations & Events
Every tutoring moment, strategy selection, adaptive assessments

### Layer 4: Insights & Predictions — ML Outputs & Teacher Support
Risk detection, grade predictions, intervention recommendations

---

## 📐 Entity Relationship Diagrams

### Layer 1: Foundation (Users & Classes)

```
┌─────────────────────────────────────────────────────────┐
│                      USERS                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ id (PK)              │ role (admin/teacher/student) │  │
│  │ first_name, last_name│ photo_url                   │  │
│  │ age, gender, ethnicity, year_level (NCEA)         │  │
│  │ learning_style       │ interests (JSON)            │  │
│  │ academic_goals       │ preferred_difficulty        │  │
│  │ learning_difficulty  │ extracurricular (JSON)      │  │
│  │ major_life_event     │ attendance_rate             │  │
│  │ date_of_birth        │ primary/secondary_language  │  │
│  │ created_at, is_active                              │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │ (teacher_id)       │ (M:M via class_users)
        ▼                    ▼
┌─────────────────────┐  ┌──────────────────────────┐
│      CLASS          │  │   CLASS_USERS (M:M)      │
│ ┌─────────────────┐ │  │ ┌────────────────────┐   │
│ │ id (PK)         │ │  │ │ class_id (PK, FK)  │   │
│ │ name            │ │  │ │ user_id (PK, FK)   │   │
│ │ description     │ │  │ │ enrolled_at        │   │
│ │ subject         │ │  │ │ is_active          │   │
│ │ teacher_id (FK) │ │  │ └────────────────────┘   │
│ │ ai_model_id(FK) │ │  └──────────────────────────┘
│ │ created_at      │ │
│ │ is_active       │ │
│ └─────────────────┘ │
└─────────────────────┘
```

---

### Layer 2: Learning Intelligence (Strategy Memory & Cache)

```
┌──────────────────────────────────────────────────────────┐
│    OPTIMIZED_PROFILE (Real-Time Cache for Tutoring)     │
│ ┌──────────────────────────────────────────────────┐    │
│ │ user_id (FK, UNIQUE)                            │    │
│ │ current_pass_rate, predicted_pass_rate          │    │
│ │ engagement_level (0-1)                          │    │
│ │ preferred_strategies (JSON) ◄── from PEDAGOG.  │    │
│ │ avoided_strategies (JSON) ◄──── from FAILED_ST │    │
│ │ struggle_areas, strength_areas                  │    │
│ │ best_time_of_day, optimal_session_length        │    │
│ └──────────────────────────────────────────────────┘    │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────┼─────────┬────────────────┐
         │         │         │                │
         ▼         ▼         ▼                ▼
    ┌────────┐ ┌──────┐ ┌──────────┐ ┌────────────────┐
    │PEDAGOG.│ │FAILED│ │STUDENT_  │ │AI_INTERACTION │
    │MEMORY  │ │STRAT.│ │WELLBEING │ │(feedback loop)│
    │        │ │      │ │CONTEXT   │ │               │
    │success │ │failure_reason    │ │success_indic. │
    │_count  │ │failure_count     │ │user_feedback  │
    │        │ │      │ │mood, stress_level        │
    │topic   │ │topic │ │sleep_quality             │
    │_area   │ │_area │ │teacher_notes             │
    │engage. │ │last_ │ │recorded_at               │
    │_score  │ │attempted         │ │created_at      │
    └────────┘ └──────┘ └──────────┘ └────────────────┘
```

**Purpose**: Every student interaction updates pedagogical memory (what works) and failed strategies (what doesn't). The cache feeds the Socratic tutor's strategy selection in real time.

---

### Layer 3: AI Interaction & Assessments

```
┌─────────────────────────────────────────┐
│           AI_MODEL                      │
│  (gpt-4o, claude-sonnet)                │
│  subject, prompt_template               │
└──────────┬────────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌──────────┐  ┌──────────────────────────┐
│CHAT_MSG  │  │AI_INTERACTION (Detailed) │
│(simple)  │  │                          │
│          │  │prompt, response          │
│message   │  │strategy_used             │
│response  │  │sub_topic (algebra, etc)  │
└──────────┘  │success_indicator         │
              │tokens_in/out             │
              │user_feedback (1-5)       │
              │linked_assignment_id      │
              │context_data              │
              └──────────────────────────┘
                       │
                       │ (generates)
                       ├─────────────────┐
                       ▼                 ▼
            ┌──────────────────┐  ┌──────────────────┐
            │  MINI_TEST       │  │MINI_TEST_RESPONSE│
            │ (Adaptive Quiz)  │  │  (Student Ans)   │
            │                  │  │                  │
            │test_type        │  │answers (JSON)   │
            │difficulty_level │  │score (%)        │
            │skills_tested    │  │time_taken       │
            │questions (JSON) │  │skill_scores     │
            └──────────────────┘  └──────────────────┘
```

---

### Layer 4: Predictions & Teacher Insights

```
┌──────────────────────────────────────┐
│   PREDICTED_GRADE                    │
│ (6 ML Models Output)                 │
│                                      │
│ current_trajectory (current grade)   │
│ predicted_final_grade (0-100)        │
│ confidence_level (0-1)               │
│ factors_analyzed (JSON)              │
│ improvement_areas, risk_factors      │
└──────────────┬───────────────────────┘
               │ (informs)
               ▼
┌──────────────────────────────────────────┐
│   TEACHER_AI_INSIGHT                     │
│ (Decision Support Cards)                 │
│                                          │
│ insight_type (at_risk/improving/etc)    │
│ summary (AI text)                        │
│ suggested_interventions (JSON)          │
│ failed_strategies ◄─ from FAILED_ST    │
│ successful_strategies ◄─ from PEDAGOG  │
│ engagement_analysis                      │
│ viewed_by_teacher, action_taken          │
└──────────────────────────────────────────┘
         ▲
         │ (aggregated from)
         └──────────────────┐
                            │
                            ▼
┌──────────────────────────────────────┐
│   PATTERN_INSIGHT                    │
│ (Cohort-Wide Learning Patterns)      │
│                                      │
│ pattern_type                         │
│ applicable_criteria (who)            │
│ recommended_strategies               │
│ success_rate (%), sample_size        │
│ confidence_level                     │
└──────────────────────────────────────┘
```

---

## 📋 Complete Table Specifications

### 👥 USERS Table
**Purpose**: Central identity and demographic data for all system roles  
**Type**: Core Foundation Entity  
**Row count in demo**: 25 students + teachers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique user identifier (demo: 1, 547–571 for students) |
| `role` | VARCHAR(20) | NOT NULL | admin \| teacher \| student |
| `first_name` | VARCHAR(50) | NOT NULL | User's given name |
| `last_name` | VARCHAR(50) | NOT NULL | User's family name |
| `photo_url` | VARCHAR(200) | NULLABLE | Avatar/profile picture URL |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account status |
| **Demographic Data** | | | |
| `age` | INTEGER | NULLABLE | Student age (years) |
| `gender` | VARCHAR(20) | NULLABLE | Male \| Female \| Other |
| `ethnicity` | VARCHAR(100) | NULLABLE | European \| Māori \| Pasifika \| Asian \| etc |
| `date_of_birth` | DATE | NULLABLE | Birth date (YYYY-MM-DD) |
| `year_level` | VARCHAR(20) | NULLABLE | Year 7–13 (NCEA: Years 11–13) |
| `primary_language` | VARCHAR(50) | NULLABLE | First language (e.g., English, Te Reo) |
| `secondary_language` | VARCHAR(50) | NULLABLE | Second language |
| `learning_difficulty` | VARCHAR(100) | NULLABLE | Dyslexia \| ADHD \| etc (support needs) |
| `extracurricular_activities` | TEXT | NULLABLE | JSON array: ["sport", "music", "debate"] |
| `major_life_event` | VARCHAR(200) | NULLABLE | Family circumstances affecting learning |
| `attendance_rate` | FLOAT | NULLABLE | Average attendance percentage (0–100) |
| **Learning Profile** | | | |
| `learning_style` | VARCHAR(50) | NULLABLE | visual \| auditory \| kinesthetic \| reading-writing |
| `interests` | TEXT | NULLABLE | JSON array of student interests |
| `academic_goals` | TEXT | NULLABLE | Student's stated goals |
| `preferred_difficulty` | VARCHAR(20) | NULLABLE | beginner \| intermediate \| advanced |

**Relationships**:
- 1:M → CLASS (as teacher)
- M:M → CLASS (as student via CLASS_USERS)
- 1:M → ASSIGNMENT_SUBMISSION
- 1:M → GRADE (as student)
- 1:M → GRADE (as teacher/grader)
- 1:M → CHAT_MESSAGE
- 1:M → AI_INTERACTION
- 1:M → TOKEN_USAGE
- 1:1 → STUDENT_PROFILE
- 1:1 → OPTIMIZED_PROFILE
- 1:M → PEDAGOGICAL_MEMORY
- 1:M → FAILED_STRATEGY
- 1:M → STUDENT_WELLBEING_CONTEXT
- 1:M → TEACHER_AI_INSIGHT (as teacher)
- 1:M → TEACHER_AI_INSIGHT (as student)

---

### 🏫 CLASS Table
**Purpose**: Course/class management aligned to NCEA curriculum  
**Type**: Core Foundation Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique class identifier |
| `name` | VARCHAR(100) | NOT NULL | Class name (e.g., "Year 11 Mathematics") |
| `description` | TEXT | NULLABLE | Curriculum overview |
| `subject` | VARCHAR(50) | NULLABLE | Subject code (Math, Biology, English, etc) |
| `teacher_id` | INTEGER | FK → users.id | Teacher responsible for class |
| `ai_model_id` | INTEGER | FK → ai_model.id | AI tutor model assigned |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Class creation time |
| `is_active` | BOOLEAN | DEFAULT TRUE | Enrollment status |

**Relationships**:
- M:1 → USER (teacher)
- 1:M → ASSIGNMENT
- 1:M → CONTENT_FILE
- M:M → USER (students via CLASS_USERS)
- M:1 → AI_MODEL
- 1:M → CHAT_MESSAGE
- 1:M → AI_INTERACTION
- 1:M → MINI_TEST
- 1:M → TEACHER_AI_INSIGHT
- 1:M → PREDICTED_GRADE

---

### 🔗 CLASS_USERS Table
**Purpose**: Enrollment bridge between students and classes  
**Type**: Association Table (Many-to-Many)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `class_id` | INTEGER | PK, FK → class.id | Class reference |
| `user_id` | INTEGER | PK, FK → user.id | Student reference |
| `enrolled_at` | TIMESTAMP | DEFAULT NOW() | Enrollment date |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active enrollment |

---

### 📝 ASSIGNMENT Table
**Purpose**: Assignment definitions for classes  
**Type**: LMS Core

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique assignment ID |
| `title` | VARCHAR(200) | NOT NULL | Assignment name |
| `description` | TEXT | NULLABLE | Instructions/requirements |
| `class_id` | INTEGER | FK → class.id | Associated class |
| `due_date` | TIMESTAMP | NULLABLE | Submission deadline |
| `max_points` | INTEGER | DEFAULT 100 | Total possible points |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `is_active` | BOOLEAN | DEFAULT TRUE | Status |

**Relationships**:
- M:1 → CLASS
- 1:M → ASSIGNMENT_SUBMISSION
- 1:M → GRADE
- 1:M → AI_INTERACTION (linked learning events)

---

### 📤 ASSIGNMENT_SUBMISSION Table
**Purpose**: Student submission records  
**Type**: LMS Core

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Submission ID |
| `assignment_id` | INTEGER | FK → assignment.id | Assignment reference |
| `student_id` | INTEGER | FK → user.id | Submitting student |
| `content` | TEXT | NULLABLE | Text/inline submission |
| `file_path` | VARCHAR(200) | NULLABLE | S3/storage path |
| `file_name` | VARCHAR(200) | NULLABLE | Original filename |
| `submitted_at` | TIMESTAMP | DEFAULT NOW() | Submission timestamp |

**Relationships**:
- M:1 → ASSIGNMENT
- M:1 → USER
- 1:1 → GRADE

---

### ⭐ GRADE Table
**Purpose**: Assessment and feedback records  
**Type**: LMS Core

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Grade ID |
| `assignment_id` | INTEGER | FK → assignment.id | Assignment reference |
| `student_id` | INTEGER | FK → user.id | Student receiving grade |
| `submission_id` | INTEGER | FK → assignment_submission.id | Submission being graded |
| `grade` | FLOAT | NULLABLE | Score (0–100 or points) |
| `feedback` | TEXT | NULLABLE | Teacher feedback |
| `graded_at` | TIMESTAMP | DEFAULT NOW() | Grading timestamp |
| `graded_by` | INTEGER | FK → user.id | Teacher who graded |

**Relationships**:
- M:1 → ASSIGNMENT
- M:1 → USER (student)
- M:1 → USER (teacher)
- 1:1 → ASSIGNMENT_SUBMISSION

---

### 📁 CONTENT_FILE Table
**Purpose**: Learning resources uploaded by teachers  
**Type**: Resource Management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | File ID |
| `class_id` | INTEGER | FK → class.id | Associated class |
| `name` | VARCHAR(200) | NOT NULL | Display name |
| `file_path` | VARCHAR(200) | NOT NULL | Storage path (S3/local) |
| `file_type` | VARCHAR(50) | NOT NULL | pdf \| slides \| txt \| video \| etc |
| `uploaded_by` | INTEGER | FK → user.id | Uploader (teacher) |
| `uploaded_at` | TIMESTAMP | DEFAULT NOW() | Upload timestamp |

**Relationships**:
- M:1 → CLASS
- M:1 → USER (uploader)
- 1:M → AI_INTERACTION (linked learning events)

---

## 🧠 Learning Intelligence Layer

### 👤 STUDENT_PROFILE Table
**Purpose**: Extended student profile for AI personalization  
**Type**: Learning Analytics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Profile ID |
| `user_id` | INTEGER | FK → user.id, UNIQUE | Student reference |
| `learning_preferences` | TEXT | NULLABLE | JSON: preferred formats, pacing |
| `study_patterns` | TEXT | NULLABLE | JSON: time_of_day, session_length, freq |
| `performance_metrics` | TEXT | NULLABLE | JSON: grades, pass_rate, trends |
| `ai_interaction_history` | TEXT | NULLABLE | JSON: tutor topics, engagement |
| `last_updated` | TIMESTAMP | DEFAULT NOW() | Last sync from live data |

**Example JSON structure**:
```json
{
  "learning_preferences": {
    "preferred_format": "visual",
    "pace": "moderate",
    "practice_ratio": 0.6
  },
  "study_patterns": {
    "best_time": "morning",
    "avg_session_minutes": 45,
    "sessions_per_week": 5
  },
  "performance_metrics": {
    "overall_gpa": 72.5,
    "pass_rate": 0.85,
    "trend": "improving"
  }
}
```

**Relationships**:
- 1:1 → USER

---

### ⚡ OPTIMIZED_PROFILE Table
**Purpose**: Real-time cached profile for low-latency AI tutoring  
**Type**: Performance Cache

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Cache ID |
| `user_id` | INTEGER | FK → user.id, UNIQUE | Student reference |
| `current_pass_rate` | FLOAT | NULLABLE | Current grade/pass rate |
| `predicted_pass_rate` | FLOAT | NULLABLE | ML prediction (0–100) |
| `engagement_level` | FLOAT | NULLABLE | 0–1 scale |
| `mastery_scores` | TEXT | NULLABLE | JSON: {skill: score} from ML |
| `best_time_of_day` | VARCHAR(20) | NULLABLE | morning \| afternoon \| evening |
| `optimal_session_length` | INTEGER | NULLABLE | Minutes |
| `preferred_strategies` | TEXT | NULLABLE | JSON array of teaching methods |
| `avoided_strategies` | TEXT | NULLABLE | JSON array of failed methods |
| `recent_topics` | TEXT | NULLABLE | JSON array of recent areas |
| `struggle_areas` | TEXT | NULLABLE | JSON array of weak skills |
| `strength_areas` | TEXT | NULLABLE | JSON array of strong skills |
| `last_updated` | TIMESTAMP | DEFAULT NOW() | Cache freshness |

**Purpose**: Eliminates O(n) profile lookups during Socratic tutoring. Synced hourly from STUDENT_PROFILE, PEDAGOGICAL_MEMORY, FAILED_STRATEGY.

**Relationships**:
- 1:1 → USER

---

### 📚 PEDAGOGICAL_MEMORY Table
**Purpose**: Persistent record of **what teaching strategies work for each student**  
**Type**: Learning Intelligence

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Memory ID |
| `user_id` | INTEGER | FK → user.id | Student reference |
| `class_id` | INTEGER | FK → class.id | Subject context |
| `strategy_name` | VARCHAR(100) | NOT NULL | e.g., "socratic_questioning", "worked_example" |
| `success_count` | INTEGER | DEFAULT 1 | Times this worked |
| `total_attempts` | INTEGER | DEFAULT 1 | Times tried |
| `success_rate` | FLOAT | NULLABLE | success_count / total_attempts |
| `topic_area` | VARCHAR(100) | NULLABLE | Skill/concept (e.g., "quadratic_equations") |
| `engagement_score` | FLOAT | NULLABLE | 0–1: student engagement during use |
| `notes` | TEXT | NULLABLE | Qualitative feedback |
| `last_used` | TIMESTAMP | NULLABLE | Most recent application |
| `created_at` | TIMESTAMP | DEFAULT NOW() | First discovery |

**Example use**: Tutor has tried "worked_example" strategy with student 3 times (success_count=2), so success_rate=0.67. AI decides to prefer this strategy for this student on similar topics.

**Relationships**:
- M:1 → USER
- M:1 → CLASS

---

### ❌ FAILED_STRATEGY Table
**Purpose**: Explicit log of teaching strategies that **did not work**  
**Type**: Learning Intelligence

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Log ID |
| `user_id` | INTEGER | FK → user.id | Student reference |
| `class_id` | INTEGER | FK → class.id | Subject context |
| `strategy_name` | VARCHAR(100) | NOT NULL | e.g., "abstract_explanation" |
| `failure_reason` | TEXT | NULLABLE | Why it failed (e.g., "too confusing") |
| `failure_count` | INTEGER | DEFAULT 1 | Number of failures |
| `last_attempted` | TIMESTAMP | DEFAULT NOW() | Most recent attempt |
| `context_data` | TEXT | NULLABLE | JSON: topic, difficulty, mood |

**Purpose**: Prevent repeating ineffective approaches. Prioritized in OPTIMIZED_PROFILE.avoided_strategies.

**Relationships**:
- M:1 → USER
- M:1 → CLASS

---

### 💚 STUDENT_WELLBEING_CONTEXT Table
**Purpose**: Track student wellbeing factors affecting learning  
**Type**: Contextual Data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Context ID |
| `user_id` | INTEGER | FK → user.id | Student reference |
| `class_id` | INTEGER | FK → class.id | Class context |
| `mood` | VARCHAR(50) | NULLABLE | happy \| neutral \| stressed \| overwhelmed |
| `stress_level` | INTEGER | NULLABLE | 1–5 scale |
| `sleep_quality` | VARCHAR(50) | NULLABLE | poor \| fair \| good \| excellent |
| `recent_absence` | BOOLEAN | DEFAULT FALSE | Recent illness/absence |
| `personal_notes` | TEXT | NULLABLE | Student self-report |
| `teacher_notes` | TEXT | NULLABLE | Teacher observation |
| `recorded_at` | TIMESTAMP | DEFAULT NOW() | Record timestamp |

**Purpose**: AI tutoring adapts pacing and tone based on student state. E.g., if stressed, avoid difficult concepts; focus on confidence-building.

**Relationships**:
- M:1 → USER
- M:1 → CLASS

---

## 🤖 AI Interaction Layer

### 🔧 AI_MODEL Table
**Purpose**: Configuration for AI tutoring models  
**Type**: AI Infrastructure

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Model ID |
| `subject` | VARCHAR(100) | NOT NULL | Mathematics \| Biology \| English \| etc |
| `model_name` | VARCHAR(200) | NOT NULL | e.g., "gpt-4o", "claude-sonnet" |
| `fine_tuned_id` | VARCHAR(200) | NULLABLE | Fine-tuned model identifier (OpenAI) |
| `prompt_template` | TEXT | NULLABLE | System prompt for Socratic tutor |
| `max_tokens` | INTEGER | DEFAULT 1000 | Max response length |
| `temperature` | FLOAT | DEFAULT 0.7 | Randomness (0–1) |
| `is_active` | BOOLEAN | DEFAULT TRUE | In use |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Relationships**:
- 1:M → CLASS
- 1:M → CHAT_MESSAGE
- 1:M → AI_INTERACTION
- 1:M → MINI_TEST

---

### 💬 CHAT_MESSAGE Table
**Purpose**: Simple conversation history between student and AI  
**Type**: Conversation Log (Basic)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Message ID |
| `user_id` | INTEGER | FK → user.id | Student |
| `class_id` | INTEGER | FK → class.id | Class context |
| `ai_model_id` | INTEGER | FK → ai_model.id | AI model used |
| `message` | TEXT | NOT NULL | Student's message |
| `response` | TEXT | NOT NULL | AI's response |
| `message_type` | VARCHAR(20) | NOT NULL | student \| teacher \| system |
| `context_data` | TEXT | NULLABLE | JSON: topic, difficulty, engagement |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Message timestamp |

**Note**: This is a basic flat message log. For threaded conversations, see CONVERSATION_THREAD and MESSAGE tables (if implemented separately).

**Relationships**:
- M:1 → USER
- M:1 → CLASS
- M:1 → AI_MODEL

---

### 🎯 AI_INTERACTION Table
**Purpose**: Detailed tracking of AI tutoring interactions  
**Type**: Tutor Analytics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Interaction ID |
| `user_id` | INTEGER | FK → user.id | Student |
| `class_id` | INTEGER | FK → class.id | Class context |
| `ai_model_id` | INTEGER | FK → ai_model.id | AI model used |
| `prompt` | TEXT | NOT NULL | Full prompt sent to AI |
| `response` | TEXT | NOT NULL | Full AI response |
| `strategy_used` | VARCHAR(100) | NULLABLE | socratic_question \| worked_example \| etc |
| `sub_topic` | VARCHAR(50) | NULLABLE | algebra \| statistics \| calculus (Math) |
| `engagement_score` | FLOAT | NULLABLE | 0–1: student engagement during |
| `tokens_in` | INTEGER | NOT NULL | Input tokens |
| `tokens_out` | INTEGER | NOT NULL | Output tokens |
| `response_time_ms` | INTEGER | NULLABLE | API latency (ms) |
| `temperature` | FLOAT | NULLABLE | Temperature used |
| `success_indicator` | BOOLEAN | NULLABLE | Did student understand? |
| `user_feedback` | INTEGER | NULLABLE | 1–5 rating (optional) |
| `linked_assignment_id` | INTEGER | FK → assignment.id | Related assignment |
| `linked_content_id` | INTEGER | FK → content_file.id | Related resource |
| `context_data` | TEXT | NULLABLE | JSON: mood, time_of_day, etc |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Interaction timestamp |

**Purpose**: Enables feedback loops. If success_indicator=TRUE for a strategy, increment PEDAGOGICAL_MEMORY. If FALSE, log to FAILED_STRATEGY.

**Relationships**:
- M:1 → USER
- M:1 → CLASS
- M:1 → AI_MODEL
- M:1 → ASSIGNMENT
- M:1 → CONTENT_FILE

---

### ❓ MINI_TEST Table
**Purpose**: Adaptive mini-tests generated by AI  
**Type**: Assessment

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Test ID |
| `class_id` | INTEGER | FK → class.id | Class context |
| `created_by_ai` | INTEGER | FK → ai_model.id | Generating model |
| `test_type` | VARCHAR(50) | NOT NULL | quiz \| diagnostic \| practice |
| `difficulty_level` | VARCHAR(20) | NOT NULL | easy \| medium \| hard |
| `skills_tested` | TEXT | NOT NULL | JSON array of skills |
| `questions` | TEXT | NOT NULL | JSON array of Q&A |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Example questions JSON**:
```json
[
  {
    "id": 1,
    "question": "Solve: 2x + 5 = 13",
    "options": ["x=4", "x=3", "x=2", "x=5"],
    "correct": 0,
    "explanation": "Subtract 5, then divide by 2"
  }
]
```

**Relationships**:
- M:1 → CLASS
- M:1 → AI_MODEL
- 1:M → MINI_TEST_RESPONSE

---

### 📊 MINI_TEST_RESPONSE Table
**Purpose**: Student responses to mini-tests  
**Type**: Assessment Results

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Response ID |
| `test_id` | INTEGER | FK → mini_test.id | Test reference |
| `user_id` | INTEGER | FK → user.id | Student |
| `answers` | TEXT | NOT NULL | JSON array of answer indices |
| `score` | FLOAT | NOT NULL | Percentage (0–100) |
| `time_taken` | INTEGER | NULLABLE | Seconds to complete |
| `skill_scores` | TEXT | NULLABLE | JSON: {skill: score} breakdown |
| `completed_at` | TIMESTAMP | DEFAULT NOW() | Completion timestamp |

**Relationships**:
- M:1 → MINI_TEST
- M:1 → USER

---

### ⏱️ TOKEN_USAGE Table
**Purpose**: Track API token consumption per student  
**Type**: Cost/Usage Analytics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Usage record ID |
| `user_id` | INTEGER | FK → user.id | Student |
| `date` | DATE | NOT NULL | Date of usage |
| `tokens_used` | INTEGER | DEFAULT 0 | Total tokens consumed |
| `requests_made` | INTEGER | DEFAULT 0 | Number of API calls |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record timestamp |

**Purpose**: Monitor per-student API costs, enforce rate limits, identify heavy users.

**Relationships**:
- M:1 → USER

---

## 📊 Insights & Predictions Layer

### 🎓 TEACHER_AI_INSIGHT Table
**Purpose**: AI-generated insights and intervention recommendations for teachers  
**Type**: Decision Support

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Insight ID |
| `class_id` | INTEGER | FK → class.id | Class context |
| `student_id` | INTEGER | FK → user.id | Student being analyzed |
| `teacher_id` | INTEGER | FK → user.id | Teacher recipient |
| `insight_type` | VARCHAR(100) | NOT NULL | at_risk \| improving \| needs_support \| high_performer |
| `summary` | TEXT | NOT NULL | AI summary of status |
| `suggested_interventions` | TEXT | NOT NULL | JSON array of recommendations |
| `failed_strategies` | TEXT | NULLABLE | JSON: what hasn't worked |
| `successful_strategies` | TEXT | NULLABLE | JSON: what has worked |
| `engagement_analysis` | TEXT | NULLABLE | JSON: patterns & trends |
| `viewed_by_teacher` | BOOLEAN | DEFAULT FALSE | Read status |
| `action_taken` | TEXT | NULLABLE | Teacher's response/notes |
| `generated_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Example interventions JSON**:
```json
[
  "Schedule 1:1 support session on quadratic equations",
  "Pair with peer tutor (student 550 strong in algebra)",
  "Increase practice: 3 mini-tests this week",
  "Consider switched pacing: move to foundational review"
]
```

**Relationships**:
- M:1 → CLASS
- M:1 → USER (student)
- M:1 → USER (teacher)

---

### 🔮 PREDICTED_GRADE Table
**Purpose**: ML predictions of final grades based on portfolio analysis  
**Type**: Predictive Analytics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Prediction ID |
| `user_id` | INTEGER | FK → user.id | Student |
| `class_id` | INTEGER | FK → class.id | Subject/class |
| `current_trajectory` | FLOAT | NOT NULL | Current grade path (0–100) |
| `predicted_final_grade` | FLOAT | NOT NULL | Predicted outcome |
| `confidence_level` | FLOAT | NOT NULL | 0–1: model confidence |
| `factors_analyzed` | TEXT | NOT NULL | JSON: what inputs drove prediction |
| `improvement_areas` | TEXT | NULLABLE | JSON: where to focus |
| `risk_factors` | TEXT | NULLABLE | JSON: what might hurt grade |
| `prediction_date` | TIMESTAMP | DEFAULT NOW() | Prediction timestamp |

**Purpose**: Sourced from the 6 ML models (mastery, risk, engagement, skill_mastery, strategy_success, progression). Used to generate TEACHER_AI_INSIGHT.

**Relationships**:
- M:1 → USER
- M:1 → CLASS

---

### 🎯 PATTERN_INSIGHT Table
**Purpose**: Global learning patterns discovered across the student cohort  
**Type**: Meta-Analytics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Pattern ID |
| `pattern_type` | VARCHAR(100) | NOT NULL | learning_style_effective \| age_group_struggle \| etc |
| `pattern_description` | TEXT | NOT NULL | Human-readable summary |
| `applicable_criteria` | TEXT | NOT NULL | JSON: who this applies to |
| `recommended_strategies` | TEXT | NOT NULL | JSON array of recommendations |
| `success_rate` | FLOAT | NULLABLE | Effectiveness percentage (0–100) |
| `sample_size` | INTEGER | NOT NULL | # of students analyzed |
| `confidence_level` | FLOAT | NULLABLE | 0–1: statistical confidence |
| `last_validated` | TIMESTAMP | DEFAULT NOW() | Last evaluation |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Discovery timestamp |

**Example pattern**:
```json
{
  "pattern_type": "kinesthetic_learners_need_movement_breaks",
  "applicable_criteria": {
    "learning_style": "kinesthetic",
    "year_level": ["Year 11", "Year 12"]
  },
  "recommended_strategies": ["5min break every 20min", "hands-on demos", "physical manipulatives"],
  "success_rate": 0.82,
  "sample_size": 23
}
```

**Purpose**: Informs teacher dashboards, AI tutor strategy selection, system-wide pedagogical improvements.

---

## 🔄 Data Flow: Socratic Tutoring Loop

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Student asks question in Socratic Tutor                        │
│                                                                  │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. Load OPTIMIZED_PROFILE (real-time cache)                    │
│     → Get student's preferred strategies                         │
│     → Get avoided_strategies (from FAILED_STRATEGY)             │
│     → Get struggle_areas, strength_areas                        │
│     → Get best_time_of_day, engagement_level                    │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. Lookup PEDAGOGICAL_MEMORY for this topic                    │
│     → SELECT top 3 strategies by success_rate                   │
│     → ORDER BY engagement_score DESC                            │
│     → Tutor decides best strategy                               │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. Tutor calls AI_MODEL with strategy                          │
│     → Prompt includes student context + chosen strategy         │
│     → AI generates Socratic question or example                 │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. AI_INTERACTION record created                               │
│     → Prompt, response, strategy_used logged                    │
│     → tokens_in/out tracked                                     │
│     → success_indicator = ? (pending feedback)                  │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. Student responds + gives feedback (1-5 stars)               │
│     → success_indicator = TRUE/FALSE                            │
│     → user_feedback = 1-5                                       │
└──────────────┬───────────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
   SUCCESS        FAILURE
        │             │
        ▼             ▼
   ┌─────────┐   ┌──────────┐
   │Increment│   │Log to    │
   │PEDAGOG. │   │FAILED_   │
   │MEMORY   │   │STRATEGY  │
   │success_ │   │failure_  │
   │count    │   │count++   │
   └────┬────┘   └────┬─────┘
        │             │
        └──────┬──────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. Invalidate OPTIMIZED_PROFILE (cache expires)                │
│     → Next query will recalculate from updated memory tables    │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  7. ML inference (via axonai-inference-api Lambda)              │
│     → Retrain 6 models (mastery, risk, engagement, etc)         │
│     → Generate PREDICTED_GRADE                                  │
│     → If risk threshold met, generate TEACHER_AI_INSIGHT       │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  8. Teacher dashboard refreshes                                 │
│     → Shows updated risk flags, insights, interventions         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Data Integrity & Foreign Keys

```sql
-- Users → Classes (teacher assignment)
ALTER TABLE class ADD CONSTRAINT fk_class_teacher 
  FOREIGN KEY (teacher_id) REFERENCES user(id);

-- Users → Classes (students via many-to-many)
ALTER TABLE class_users ADD CONSTRAINT fk_class_users_class 
  FOREIGN KEY (class_id) REFERENCES class(id);
ALTER TABLE class_users ADD CONSTRAINT fk_class_users_user 
  FOREIGN KEY (user_id) REFERENCES user(id);

-- Assignment → Class
ALTER TABLE assignment ADD CONSTRAINT fk_assignment_class 
  FOREIGN KEY (class_id) REFERENCES class(id);

-- Submission → Assignment, Student
ALTER TABLE assignment_submission ADD CONSTRAINT fk_submission_assignment 
  FOREIGN KEY (assignment_id) REFERENCES assignment(id);
ALTER TABLE assignment_submission ADD CONSTRAINT fk_submission_student 
  FOREIGN KEY (student_id) REFERENCES user(id);

-- Grade → Student, Assignment, Submission, Teacher
ALTER TABLE grade ADD CONSTRAINT fk_grade_student 
  FOREIGN KEY (student_id) REFERENCES user(id);
ALTER TABLE grade ADD CONSTRAINT fk_grade_assignment 
  FOREIGN KEY (assignment_id) REFERENCES assignment(id);
ALTER TABLE grade ADD CONSTRAINT fk_grade_submission 
  FOREIGN KEY (submission_id) REFERENCES assignment_submission(id);
ALTER TABLE grade ADD CONSTRAINT fk_grade_teacher 
  FOREIGN KEY (graded_by) REFERENCES user(id);

-- AI Interactions
ALTER TABLE chat_message ADD CONSTRAINT fk_chat_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE chat_message ADD CONSTRAINT fk_chat_class 
  FOREIGN KEY (class_id) REFERENCES class(id);
ALTER TABLE chat_message ADD CONSTRAINT fk_chat_ai_model 
  FOREIGN KEY (ai_model_id) REFERENCES ai_model(id);

ALTER TABLE ai_interaction ADD CONSTRAINT fk_ai_interaction_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE ai_interaction ADD CONSTRAINT fk_ai_interaction_class 
  FOREIGN KEY (class_id) REFERENCES class(id);
ALTER TABLE ai_interaction ADD CONSTRAINT fk_ai_interaction_ai_model 
  FOREIGN KEY (ai_model_id) REFERENCES ai_model(id);
ALTER TABLE ai_interaction ADD CONSTRAINT fk_ai_interaction_assignment 
  FOREIGN KEY (linked_assignment_id) REFERENCES assignment(id);
ALTER TABLE ai_interaction ADD CONSTRAINT fk_ai_interaction_content 
  FOREIGN KEY (linked_content_id) REFERENCES content_file(id);

-- Learning Intelligence
ALTER TABLE student_profile ADD CONSTRAINT fk_student_profile_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE optimized_profile ADD CONSTRAINT fk_optimized_profile_user 
  FOREIGN KEY (user_id) REFERENCES user(id);

ALTER TABLE pedagogical_memory ADD CONSTRAINT fk_ped_memory_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE pedagogical_memory ADD CONSTRAINT fk_ped_memory_class 
  FOREIGN KEY (class_id) REFERENCES class(id);

ALTER TABLE failed_strategy ADD CONSTRAINT fk_failed_strategy_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE failed_strategy ADD CONSTRAINT fk_failed_strategy_class 
  FOREIGN KEY (class_id) REFERENCES class(id);

ALTER TABLE student_wellbeing_context ADD CONSTRAINT fk_wellbeing_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE student_wellbeing_context ADD CONSTRAINT fk_wellbeing_class 
  FOREIGN KEY (class_id) REFERENCES class(id);

-- Predictions & Insights
ALTER TABLE teacher_ai_insight ADD CONSTRAINT fk_insight_class 
  FOREIGN KEY (class_id) REFERENCES class(id);
ALTER TABLE teacher_ai_insight ADD CONSTRAINT fk_insight_student 
  FOREIGN KEY (student_id) REFERENCES user(id);
ALTER TABLE teacher_ai_insight ADD CONSTRAINT fk_insight_teacher 
  FOREIGN KEY (teacher_id) REFERENCES user(id);

ALTER TABLE predicted_grade ADD CONSTRAINT fk_predicted_grade_user 
  FOREIGN KEY (user_id) REFERENCES user(id);
ALTER TABLE predicted_grade ADD CONSTRAINT fk_predicted_grade_class 
  FOREIGN KEY (class_id) REFERENCES class(id);
```

---

## 📈 Query Optimization

### Recommended Indexes

```sql
-- Users
CREATE INDEX idx_users_active ON user(is_active);
CREATE INDEX idx_users_role ON user(role);

-- Classes & enrollment
CREATE INDEX idx_class_teacher ON class(teacher_id);
CREATE INDEX idx_class_active ON class(is_active);
CREATE INDEX idx_class_users_user ON class_users(user_id);
CREATE INDEX idx_class_users_class ON class_users(class_id);

-- Learning data
CREATE INDEX idx_ai_interaction_user_class ON ai_interaction(user_id, class_id);
CREATE INDEX idx_ai_interaction_date ON ai_interaction(created_at DESC);
CREATE INDEX idx_student_profile_user ON student_profile(user_id);
CREATE INDEX idx_optimized_profile_user ON optimized_profile(user_id);

-- Pedagogical memory
CREATE INDEX idx_ped_memory_user_topic ON pedagogical_memory(user_id, topic_area);
CREATE INDEX idx_ped_memory_success ON pedagogical_memory(success_rate DESC);
CREATE INDEX idx_failed_strategy_user ON failed_strategy(user_id);

-- Insights & predictions
CREATE INDEX idx_teacher_insight_class_student ON teacher_ai_insight(class_id, student_id);
CREATE INDEX idx_predicted_grade_user_class ON predicted_grade(user_id, class_id);

-- Well-being
CREATE INDEX idx_wellbeing_user_date ON student_wellbeing_context(user_id, recorded_at DESC);

-- Chat/interaction
CREATE INDEX idx_chat_user_class ON chat_message(user_id, class_id);
CREATE INDEX idx_chat_date ON chat_message(created_at DESC);

-- Assignments
CREATE INDEX idx_assignment_class ON assignment(class_id);
CREATE INDEX idx_submission_assignment ON assignment_submission(assignment_id);
CREATE INDEX idx_grade_student ON grade(student_id);
```

---

## 🔍 Common Query Patterns

### Teacher Dashboard — Student Overview
```sql
-- Get all students in teacher's classes with risk assessments
SELECT 
  u.id, u.first_name, u.last_name,
  pg.predicted_final_grade,
  tài.insight_type,
  op.engagement_level,
  op.struggle_areas
FROM user u
JOIN class_users cu ON u.id = cu.user_id
JOIN class c ON cu.class_id = c.id
LEFT JOIN predicted_grade pg ON u.id = pg.user_id AND pg.class_id = c.id
LEFT JOIN teacher_ai_insight tài ON u.id = tài.student_id AND tài.class_id = c.id
LEFT JOIN optimized_profile op ON u.id = op.user_id
WHERE c.teacher_id = ? AND cu.is_active = true
ORDER BY COALESCE(pg.predicted_final_grade, 0) ASC;
```

### Student Learning Journey — Mastery Progression
```sql
-- Track student's mastery growth over time
SELECT 
  ai.created_at,
  ai.sub_topic,
  ai.strategy_used,
  ai.success_indicator,
  pm.success_rate
FROM ai_interaction ai
LEFT JOIN pedagogical_memory pm ON ai.user_id = pm.user_id 
  AND ai.strategy_used = pm.strategy_name 
  AND ai.sub_topic = pm.topic_area
WHERE ai.user_id = ? AND ai.class_id = ?
ORDER BY ai.created_at ASC;
```

### Tutor Strategy Selection
```sql
-- Get best strategies for this student on this topic
SELECT 
  pm.strategy_name,
  pm.success_rate,
  pm.engagement_score,
  pm.last_used
FROM pedagogical_memory pm
WHERE pm.user_id = ? AND pm.topic_area ILIKE ?
ORDER BY pm.success_rate DESC, pm.engagement_score DESC
LIMIT 3;
```

### Risk Flagging — At-Risk Students
```sql
-- Identify students at risk in real time
SELECT 
  u.id, u.first_name, u.last_name,
  op.current_pass_rate,
  op.predicted_pass_rate,
  tài.suggested_interventions,
  CASE 
    WHEN op.predicted_pass_rate < 40 THEN 'CRITICAL'
    WHEN op.predicted_pass_rate < 60 THEN 'HIGH'
    WHEN op.predicted_pass_rate < 75 THEN 'MEDIUM'
    ELSE 'LOW'
  END as risk_level
FROM user u
JOIN class_users cu ON u.id = cu.user_id
JOIN optimized_profile op ON u.id = op.user_id
LEFT JOIN teacher_ai_insight tài ON u.id = tài.student_id
WHERE cu.class_id = ? 
  AND cu.is_active = true
  AND op.predicted_pass_rate < 75
ORDER BY op.predicted_pass_rate ASC;
```

### Well-being Context — Support Planning
```sql
-- Check student state for tutoring adaptation
SELECT 
  swc.mood, swc.stress_level, swc.sleep_quality,
  swc.teacher_notes, swc.recorded_at
FROM student_wellbeing_context swc
WHERE swc.user_id = ? AND swc.class_id = ?
ORDER BY swc.recorded_at DESC
LIMIT 1;
```

---

## 🏢 Database Configuration

**PostgreSQL Version**: 17+  
**Connection Pool**: 20 max connections (Lambda environment)  
**Timezone**: UTC (all timestamps)  
**Character Set**: UTF-8 (supports Te Reo Māori, multilingual)

### AWS RDS Setup
- **Engine**: postgres
- **Instance**: db.t3.small (demo) / db.t3.medium+ (production)
- **Storage**: 20 GB gp3, auto-scaling
- **Region**: ap-southeast-2 (Auckland)
- **Backup**: Daily snapshots, 7-day retention
- **Secrets Manager**: `axonai/db/credentials`

---

## 🔄 Data Sync & ML Integration

### Predictive Models (6 ML Models)
These models are trained on Supabase (separate environment) and served via `axonai-inference-api` Lambda:

1. **Mastery Model** (LogisticRegression) — predicts concept mastery (0–1)
2. **Risk Model** (LogisticRegression) — predicts fail risk (True/False)
3. **Engagement Model** (Ridge) — predicts engagement level (0–1)
4. **Skill Mastery Model** (Ridge) — predicts sub-skill score
5. **Strategy Success Model** (LogisticRegression) — predicts if strategy works
6. **Progression Model** (LogisticRegression) — predicts learning progression

**Flow**:
1. ML worker on Modal/Supabase retrains models every 2 minutes
2. Models serialized → Supabase Storage
3. `axonai-inference-api` Lambda loads + caches models
4. Teacher/Student dashboards call inference endpoint
5. Results populate PREDICTED_GRADE, TEACHER_AI_INSIGHT, OPTIMIZED_PROFILE

### Real-Time Data Flow
```
Student uses Socratic Tutor
  → AI_INTERACTION written
  → Token usage logged (TOKEN_USAGE)
  → Success/failure → PEDAGOGICAL_MEMORY or FAILED_STRATEGY
  → OPTIMIZED_PROFILE invalidated (refresh next sync)
  → ML inference Lambda called
  → PREDICTED_GRADE updated
  → TEACHER_AI_INSIGHT generated if threshold met
  → Dashboard refreshes
```

---

## 🛡️ Privacy & GDPR Compliance

- All PII (names, emails, dates of birth) encrypted at rest (AWS KMS)
- Wellbeing data (mood, stress) flagged as sensitive
- Audit trail: `created_at`, `last_updated` on all sensitive tables
- Data retention: 7 years (NCEA requirement), then anonymization
- GDPR: Full export & deletion workflows for STUDENT_PROFILE, AI_INTERACTION

---

## ✅ Schema Validation

Run this check to verify all FKs are valid:
```sql
-- Check for orphaned records
SELECT * FROM ai_interaction WHERE user_id NOT IN (SELECT id FROM user);
SELECT * FROM teacher_ai_insight WHERE student_id NOT IN (SELECT id FROM user);
SELECT * FROM predicted_grade WHERE class_id NOT IN (SELECT id FROM class);
```

---

## 📝 Design Philosophy

AxonAI's database is **cognitive infrastructure**, not a traditional LMS. Key principles:

1. **Every interaction feeds memory**: AI_INTERACTION → PEDAGOGICAL_MEMORY (success) or FAILED_STRATEGY (failure)
2. **Memory drives strategy**: Next tutoring decision loads OPTIMIZED_PROFILE + PEDAGOGICAL_MEMORY
3. **Insights emerge automatically**: PREDICTED_GRADE + TEACHER_AI_INSIGHT generated from ML predictions
4. **Feedback loops are tight**: Student response → strategy update → ML retrain → teacher alert (all within seconds)
5. **Data is rich & contextual**: Demographics, wellbeing, engagement, strategy effectiveness all tracked
6. **Teacher augmentation, not replacement**: AI surfaces insights; humans decide actions

---

**Schema Last Updated**: 2026-04-07  
**Maintainer**: AxonAI Product Team  
**Contact**: design@axonai.nz
