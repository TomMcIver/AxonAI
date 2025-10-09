# Simple Local AI Tutoring System

A local tutoring system with SQLite database featuring two agents:
- **Main Tutor Agent** - Manages student profiles and chat sessions
- **Mastery Tracking Agent** - Analyzes learning patterns and tracks topic mastery

Fully local with no external API calls.

## 📁 Files

### Core System
- **`database_setup.py`** - Creates the `school_ai.db` SQLite database
- **`migrate_add_mastery_fields.py`** - Adds mastery tracking fields to database

### Agents
- **`main_tutor_agent.py`** - Main Tutor Agent (Agent 1) - Chat and interaction management
- **`mastery_tracking_agent.py`** - Mastery Tracking Agent (Agent 2) - Learning analysis

### Interface & Tests
- **`tutor_cli.py`** - Interactive command-line interface for both agents
- **`test_tutor.py`** - Test script for Main Tutor Agent
- **`test_both_agents.py`** - Integration test for both agents

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

### 4. Run Database Migration (if needed)
```bash
python3 migrate_add_mastery_fields.py
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

## 🎯 Features

- **Fully Local**: No external AI APIs - uses rule-based responses
- **Subject-Aware**: Different response patterns for Math, Science, English, History
- **Understanding Score**: Automatically increases with each interaction (0.0 to 10.0)
- **Complete History**: All chat interactions stored in JSON format
- **Timestamp Tracking**: Tracks creation, updates, and last interaction times
- **Topic Mastery Tracking**: Analyzes chat to identify topic-specific understanding
- **Learning Trend Detection**: Detects if student is improving, declining, or staying flat
- **Simple CLI**: Easy-to-use command-line interface for both agents

## 💡 Understanding Score

The understanding score is a simple placeholder that:
- Starts at 0.0 for new students
- Increases by 0.1 with each interaction
- Caps at 10.0 maximum
- Can be replaced with more sophisticated logic later

## 🔧 Example Usage

### Basic Usage with Both Agents
```python
from main_tutor_agent import MainTutorAgent
from mastery_tracking_agent import MasteryTrackingAgent

# Initialize both agents
tutor = MainTutorAgent()
tracker = MasteryTrackingAgent()

# Create a student
student_id = tutor.create_student("Bob Smith", "Science")

# Have a conversation
tutor.generate_response(student_id, "What is photosynthesis?")
tutor.generate_response(student_id, "I understand! It's how plants make energy")
tutor.generate_response(student_id, "Can you explain cellular respiration?")

# Analyze mastery
tracker.update_student_mastery(student_id)

# Get mastery report
report = tracker.get_mastery_report(student_id)
print(f"Learning Trend: {report['trend']}")
print(f"Topic Mastery: {report['mastery_levels']}")
```

## 📊 Sample Output

```
✓ Created student profile: Bob Smith (ID: 1) - Subject: Science
✓ Recorded interaction for student ID 1
  Understanding score: 0.0 → 0.1
✓ Recorded interaction for student ID 1
  Understanding score: 0.1 → 0.2
```

## 🔄 Next Steps

This system now includes:
- ✅ Agent 1: Main Tutor Agent (chat and interaction management)
- ✅ Agent 2: Mastery Tracking Agent (learning analysis and trend detection)

Future enhancements:
- Agent 3: Strategy Optimizer (recommends personalized teaching approaches)
- Quiz generation and assessment tracking
- More sophisticated mastery calculations
- Advanced AI integration (when needed)
