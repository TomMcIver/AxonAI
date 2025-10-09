# Simple Local AI Tutoring System

A local tutoring system with SQLite database featuring three agents:
- **Main Tutor Agent** (Agent 1) - Manages student profiles and chat sessions
- **Mastery Tracking Agent** (Agent 2) - Analyzes learning patterns and tracks topic mastery
- **Quiz/Exam Builder** (Agent 3) - Generates adaptive quizzes and tracks performance

Fully local with no external API calls.

## 📁 Files

### Core System
- **`database_setup.py`** - Creates the `school_ai.db` SQLite database
- **`migrate_add_mastery_fields.py`** - Adds mastery tracking fields to database
- **`migrate_add_quizzes_table.py`** - Adds quizzes table to database

### Agents
- **`main_tutor_agent.py`** - Main Tutor Agent (Agent 1) - Chat and interaction management
- **`mastery_tracking_agent.py`** - Mastery Tracking Agent (Agent 2) - Learning analysis
- **`quiz_builder_agent.py`** - Quiz/Exam Builder (Agent 3) - Adaptive quiz generation

### Interface & Tests
- **`tutor_cli.py`** - Interactive command-line interface for all three agents
- **`test_tutor.py`** - Test script for Main Tutor Agent
- **`test_both_agents.py`** - Integration test for Agents 1 & 2
- **`test_all_three_agents.py`** - Comprehensive test for all three agents

## 🗄️ Database Schema

**Table: `student_profiles`**

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing student ID |
| name | TEXT | Student's name |
| subject | TEXT | Subject they're studying |
| last_interaction | TEXT | Timestamp of last interaction |
| chat_history | TEXT (JSON) | Complete chat history as JSON array |
| understanding_score | REAL | Score from 0.0 to 10.0 |
| **mastery_levels** | **TEXT (JSON)** | **Topic-wise mastery percentages** |
| **trend** | **TEXT** | **Learning trend: "up", "flat", or "down"** |
| created_at | TEXT | Timestamp when profile was created |
| updated_at | TEXT | Timestamp when profile was last updated |

**Table: `quizzes`**

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing quiz ID |
| student_id | INTEGER | Foreign key to student_profiles.id |
| topic | TEXT | Quiz topic (based on weak areas) |
| questions | TEXT (JSON) | Array of quiz questions |
| answers | TEXT (JSON) | Array of student answers |
| score | REAL | Quiz score (0-100 percentage) |
| created_at | TEXT | Timestamp when quiz was created |

## 🚀 Quick Start

### 1. Create the Database
```bash
python3 database_setup.py
```

### 2. Run the CLI Interface
```bash
python3 tutor_cli.py
```

### 3. Run Tests
```bash
# Test Main Tutor Agent only
python3 test_tutor.py

# Test both agents integrated
python3 test_both_agents.py
```

### 4. Run Database Migrations (if needed)
```bash
# Add mastery tracking fields
python3 migrate_add_mastery_fields.py

# Add quizzes table
python3 migrate_add_quizzes_table.py
```

## 📚 Main Tutor Agent Functions

### `create_student(name, subject)`
Creates a new student profile.
```python
from main_tutor_agent import MainTutorAgent

agent = MainTutorAgent()
student_id = agent.create_student("Alice Johnson", "Math")
```

### `record_interaction(student_id, user_message, ai_response)`
Records a chat interaction and updates the student profile.
```python
agent.record_interaction(
    student_id=1,
    user_message="How do I solve x + 5 = 10?",
    ai_response="Let's break it down step by step..."
)
```

### `get_chat_history(student_id)`
Retrieves the complete chat history for a student.
```python
history = agent.get_chat_history(student_id=1)
# Returns: [{"timestamp": "...", "user": "...", "tutor": "..."}, ...]
```

### `get_student_profile(student_id)`
Gets the complete student profile with all fields.
```python
profile = agent.get_student_profile(student_id=1)
# Returns: {"id": 1, "name": "...", "subject": "...", "chat_history": [...], ...}
```

### `generate_response(student_id, user_message)`
Generates a tutor response and automatically records the interaction.
```python
response = agent.generate_response(student_id=1, user_message="I need help")
```

## 🔬 Mastery Tracking Agent Functions

### `update_student_mastery(student_id)`
Analyzes chat history and updates mastery tracking fields.
```python
from mastery_tracking_agent import MasteryTrackingAgent

tracker = MasteryTrackingAgent()
tracker.update_student_mastery(student_id=1)
```

**What it does:**
- Reads chat_history from database
- Analyzes interaction quality (positive/negative indicators, engagement)
- Identifies topics discussed based on subject keywords
- Calculates topic-wise mastery percentages
- Detects learning trend (up/flat/down)
- Updates mastery_levels and trend in database

### `get_mastery_report(student_id)`
Gets a formatted mastery report for a student.
```python
report = tracker.get_mastery_report(student_id=1)
# Returns: {
#   'student_id': 1,
#   'name': '...',
#   'subject': '...',
#   'mastery_levels': {'algebra': {'percentage': 65.0, 'interactions': 5}},
#   'trend': 'up',
#   ...
# }
```

### Analysis Logic
The Mastery Tracking Agent uses:

**Positive Indicators**: 'yes', 'got it', 'understand', 'thanks', 'clear', 'makes sense', etc.

**Negative Indicators**: 'no', 'confused', "don't understand", 'help', 'stuck', 'lost', etc.

**Topic Keywords**: Subject-specific keywords for:
- **Math**: algebra, geometry, arithmetic, calculus
- **Science**: biology, chemistry, physics
- **English**: grammar, writing, literature
- **History**: ancient, modern, american

**Trend Detection**: Compares average mastery percentage with previous analysis:
- **up**: Improved by more than 2%
- **down**: Declined by more than 2%
- **flat**: Changed less than 2%

## 🎯 Quiz/Exam Builder Functions

### `generate_quiz(student_id, num_questions=5)`
Generates an adaptive quiz based on student's weakest topics.
```python
from quiz_builder_agent import QuizBuilderAgent

builder = QuizBuilderAgent()
quiz_id = builder.generate_quiz(student_id=1, num_questions=5)
```

**What it does:**
- Identifies student's weakest topics from mastery_levels
- Selects questions from hardcoded question bank
- Generates 5 questions (default) targeting weak areas
- Stores quiz in database
- Returns quiz ID

### `submit_quiz(quiz_id, student_answers)`
Submits quiz answers and updates student profile.
```python
answers = ['4', '0.2', '4', '5', '25']  # Student's answers
results = builder.submit_quiz(quiz_id=1, student_answers=answers)
# Returns: {
#   'correct': 5,
#   'total': 5,
#   'score': 100.0,
#   'old_understanding': 2.5,
#   'new_understanding': 4.75
# }
```

**What it does:**
- Compares answers with correct answers
- Calculates score percentage
- Updates understanding_score (weighted: 70% current + 30% quiz)
- Returns detailed results

### `get_weakest_topics(student_id, limit=3)`
Identifies student's weakest topics for targeted learning.
```python
weak_topics = builder.get_weakest_topics(student_id=1, limit=3)
# Returns: [('arithmetic', 53.0), ('general', 59.0), ('algebra', 65.0)]
```

### Question Bank
The Quiz Builder includes **100+ hardcoded questions** covering:

**Math Topics:**
- Algebra (solving equations, variables)
- Geometry (area, perimeter, angles)
- Arithmetic (addition, multiplication, fractions)
- General (powers, percentages, square roots)

**Science Topics:**
- Biology (cells, photosynthesis, DNA)
- Chemistry (elements, compounds, pH)
- Physics (forces, motion, energy)
- General (scientific concepts)

**English Topics:**
- Grammar (parts of speech, tenses)
- Writing (paragraphs, punctuation)
- Literature (themes, literary devices)
- General (language fundamentals)

**History Topics:**
- Ancient (Egypt, Rome, Greece, China)
- Modern (wars, inventions, revolutions)
- American (independence, constitution, civil war)
- General (historical events)

## 🎯 Features

- **Fully Local**: No external AI APIs - uses rule-based responses and hardcoded questions
- **Subject-Aware**: Different response patterns for Math, Science, English, History
- **Understanding Score**: Automatically increases with each interaction (0.0 to 10.0)
- **Complete History**: All chat interactions stored in JSON format
- **Timestamp Tracking**: Tracks creation, updates, and last interaction times
- **Topic Mastery Tracking**: Analyzes chat to identify topic-specific understanding
- **Learning Trend Detection**: Detects if student is improving, declining, or staying flat
- **Adaptive Quizzes**: Generates quizzes targeting student's weakest topics
- **Quiz Scoring**: Automatic grading and understanding score updates
- **Quiz History**: Tracks all quiz attempts with scores and topics
- **Simple CLI**: Easy-to-use command-line interface for all three agents

## 💡 Understanding Score

The understanding score is a simple placeholder that:
- Starts at 0.0 for new students
- Increases by 0.1 with each interaction
- Caps at 10.0 maximum
- Can be replaced with more sophisticated logic later

## 🔧 Example Usage

### Complete Workflow with All Three Agents
```python
from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent
from quiz_builder_agent import QuizBuilderAgent

# Initialize all three agents
tutor = MainTutorAgent()
tracker = MasteryTrackingAgent()
quiz_builder = QuizBuilderAgent()

# Step 1: Create a student (Agent 1)
student_id = tutor.create_student("Bob Smith", "Science")

# Step 2: Have a learning conversation (Agent 1)
tutor.generate_response(student_id, "What is photosynthesis?")
tutor.generate_response(student_id, "I understand! It's how plants make energy")
tutor.generate_response(student_id, "Can you explain cellular respiration?")

# Step 3: Analyze mastery and identify weak topics (Agent 2)
tracker.update_student_mastery(student_id)
report = tracker.get_mastery_report(student_id)
print(f"Learning Trend: {report['trend']}")
print(f"Weak Topics: {report['mastery_levels']}")

# Step 4: Generate adaptive quiz targeting weak areas (Agent 3)
quiz_id = quiz_builder.generate_quiz(student_id, num_questions=5)

# Step 5: Student takes the quiz (Agent 3)
quiz = quiz_builder.get_quiz(quiz_id)
answers = ['mitochondria', 'photosynthesis', 'deoxyribonucleic acid', 'red blood cells', '46']

# Step 6: Submit and score quiz (Agent 3)
results = quiz_builder.submit_quiz(quiz_id, answers)
print(f"Score: {results['score']}%")
print(f"Understanding updated: {results['old_understanding']} → {results['new_understanding']}")
```

## 📊 Sample Output

```
✓ Created student profile: Bob Smith (ID: 1) - Subject: Science
✓ Recorded interaction for student ID 1
  Understanding score: 0.0 → 0.1
✓ Recorded interaction for student ID 1
  Understanding score: 0.1 → 0.2
```

## 🔄 System Status

This system now includes:
- ✅ Agent 1: Main Tutor Agent (chat and interaction management)
- ✅ Agent 2: Mastery Tracking Agent (learning analysis and trend detection)
- ✅ Agent 3: Quiz/Exam Builder (adaptive quiz generation and scoring)

All three agents are fully integrated and working together!

Future enhancements:
- More sophisticated mastery calculations
- Expanded question bank with more topics
- Performance analytics and reporting
- Advanced AI integration (when needed)
