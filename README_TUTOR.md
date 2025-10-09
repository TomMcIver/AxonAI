# Simple Local AI Tutoring System

A basic tutoring system with SQLite database and a Main Tutor Agent that manages student profiles and chat sessions - fully local with no external API calls.

## 📁 Files

- **`database_setup.py`** - Creates the `school_ai.db` SQLite database
- **`main_tutor_agent.py`** - Main Tutor Agent class with core functionality
- **`tutor_cli.py`** - Interactive command-line interface
- **`test_tutor.py`** - Test script demonstrating all features

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

### 3. Or Run Tests
```bash
python3 test_tutor.py
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

## 🎯 Features

- **Fully Local**: No external AI APIs - uses rule-based responses
- **Subject-Aware**: Different response patterns for Math, Science, English, History
- **Understanding Score**: Automatically increases with each interaction (0.0 to 10.0)
- **Complete History**: All chat interactions stored in JSON format
- **Timestamp Tracking**: Tracks creation, updates, and last interaction times
- **Simple CLI**: Easy-to-use command-line interface for testing

## 💡 Understanding Score

The understanding score is a simple placeholder that:
- Starts at 0.0 for new students
- Increases by 0.1 with each interaction
- Caps at 10.0 maximum
- Can be replaced with more sophisticated logic later

## 🔧 Example Usage

```python
from main_tutor_agent import MainTutorAgent

# Initialize agent
agent = MainTutorAgent()

# Create a student
student_id = agent.create_student("Bob Smith", "Science")

# Have a conversation
response1 = agent.generate_response(student_id, "What is photosynthesis?")
response2 = agent.generate_response(student_id, "How does it work?")

# Get chat history
history = agent.get_chat_history(student_id)
print(f"Total interactions: {len(history)}")

# Get profile
profile = agent.get_student_profile(student_id)
print(f"Understanding score: {profile['understanding_score']}")
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

This is the foundation for:
- Agent 2: Learning Analysis Agent (analyzes patterns, identifies weaknesses)
- Agent 3: Strategy Optimizer (recommends teaching approaches)
- More sophisticated understanding score calculations
- Advanced AI integration (when needed)
