# AxonAI Demo - Minimal Learning Loop

## Overview
This demo showcases the core AxonAI adaptive learning loop with three key components:

1. **AI Tutor Chat** - Students interact with an AI tutor personalized to their profile
2. **Adaptive Quizzes** - Generate quizzes based on class subject
3. **Mastery Tracking** - Track skill mastery that updates after each quiz

## Demo Loop

```
Student asks question → AI Tutor responds with personalized help
       ↓
Student takes quiz → Quiz generated from question bank
       ↓
Submit answers → Score calculated, mastery updated
       ↓
Mastery levels → Displayed on student dashboard
```

## API Endpoints

### Chat
- `POST /api/chat` - Send message to AI tutor
  - Body: `{class_id: int, message: string}`
  - Returns: `{success: bool, response: string}`

### Quiz
- `POST /api/quiz/generate` - Generate a quiz
  - Body: `{class_id: int, num_questions: int}`
  - Returns: `{success: bool, quiz_id: int, questions: array}`

- `POST /api/quiz/submit` - Submit quiz answers
  - Body: `{quiz_id: int, answers: array}`
  - Returns: `{success: bool, score: float, results: array, mastery_updated: object}`

### Mastery
- `GET /api/student/mastery` - Get mastery levels
  - Returns: `{success: bool, mastery: object, recent_quizzes: array}`

## Model Interfaces

The demo uses swappable model interfaces located in `services/model_interfaces.py`:

- `BaseTutorModel` - Interface for AI tutoring
- `BaseQuizModel` - Interface for quiz generation
- `BaseGraderModel` - Interface for grading
- `BaseMasteryModel` - Interface for mastery calculation
- `BaseProfileModel` - Interface for profile summarization

### Default Implementations
- `GPTTutorModel` - Uses OpenAI GPT-4o for tutoring
- `GPTProfileModel` - Uses GPT for profile summaries
- `SimpleMasteryModel` - Simple weighted average mastery calculation

## Running the Demo

1. Start the application: The app runs on port 5000
2. Login as a student
3. Navigate to Student Dashboard
4. Use the "AI Learning Demo" section to:
   - View your mastery levels
   - Take quizzes for enrolled classes
   - See your scores and mastery updates

## Smoke Test

Run the smoke test to verify endpoints:

```bash
python scripts/smoke_demo.py
```

## Database Models

The demo uses these PostgreSQL models:
- `MiniTest` - Stores generated quizzes
- `MiniTestResponse` - Stores student quiz responses
- `OptimizedProfile` - Caches mastery scores for fast access

## Question Bank

Questions are stored in `api_routes.py` in the `QUESTION_BANK` dictionary, organized by:
- Subject (math, science, english, history)
- Topic (algebra, geometry, biology, etc.)

## Next Steps

To extend the demo:
1. Add GPT-based quiz generation (replace hardcoded question bank)
2. Implement adaptive difficulty based on mastery
3. Add strategy tracking for teaching approaches
4. Connect to Big AI Coordinator for pattern analysis
