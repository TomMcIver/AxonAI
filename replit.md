# TMC Learning

## Overview
TMC Learning is a Flask-based learning management platform designed to provide a comprehensive educational experience with role-based access control for administrators, teachers, and students. Its core purpose is to offer personalized learning through an innovative Dual-AI architecture, ensuring every student receives tailored support and teachers gain actionable insights. The platform aims to revolutionize education by integrating advanced AI tutoring capabilities, making it a powerful tool for modern learning environments.

## User Preferences
Preferred communication style: Simple, everyday language.

Design preferences: Grayscale color scheme, flat 2D design with depth (like 2D games), no rounded buttons, everything angular and geometric.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework
- **Database ORM**: SQLAlchemy with declarative base model
- **Database**: PostgreSQL 17 (production-ready)
- **Authentication**: Session-based with bcrypt password hashing
- **Authorization**: Role-based access control (admin, teacher, student)

### Frontend Architecture
- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **Client-side**: Vanilla JavaScript with Bootstrap components

### Security Architecture
- **Password Security**: bcrypt hashing with salt
- **Session Management**: Flask sessions with secret key
- **Access Control**: Decorator-based role authorization
- **Input Validation**: Server-side form validation

### Dual-AI Architecture
- **Individual AI Tutors**: Self-optimizing AI for each student, learning continuously, adapting strategies (10+ methods), avoiding failed approaches, updating `OptimizedProfile` in real-time, generating mini-tests, and predicting outcomes.
- **Big AI Coordinator**: Analyzes global patterns across students, identifies best practices, pushes improvements to individual tutors, generates teacher insights and risk alerts, and optimizes collectively.
- **Three-Layer Data Model**: Raw database for interaction history (`AIInteraction`, `FailedStrategy`, `MiniTest`, `PatternInsight`, `PredictedGrade`, `TeacherAIInsight`), optimized profile for fast working memory, and a failed strategies log.
- **Feedback Loop**: Student Interaction → Individual AI Tutor → Store Results → Choose Strategy → Optimize Profile ← Big AI Patterns → Track Success → Aggregate Analysis.

### Key Features
- **Predicted Pass Rates**: AI analyzes student portfolios.
- **Subject-Specific Tutors**: Focused AI models for various subjects (Math, Science, English, History).
- **Mini-Test Generation**: Adaptive difficulty based on performance.
- **Strategy Experimentation**: 10 teaching methods tracked for success.
- **Teacher AI Assistant**: Summarizes progress, suggests interventions.
- **Advanced Export System**: Selective data export with relationship visualization and CSV generation.
- **Multi-Topic Progression Tracking**: Advanced visualization system showing student understanding across multiple math topics (Algebra, Statistics, Calculus) with adaptive composite scoring that maintains context when switching topics.

### Multi-Topic Progression System (October 2025)

**Purpose**: Demonstrate adaptive AI capabilities by tracking student understanding across multiple math sub-topics while maintaining overall context.

**Architecture**:
- **Sub-Topic Tracking**: Each AIInteraction records which sub-topic (algebra/statistics/calculus) was studied
- **Adaptive Composite Scoring**: Uses weighted algorithm to prevent understanding drops when switching topics
  - New topics (<10 interactions): Gradual weight increase (10% per interaction)
  - Established topics (10+ interactions): Full weight (100%)
  - Formula: `composite_score = Σ(topic_mastery × weight) / Σ(weight)`
- **Independent Progression Views**: Separate tracking for each sub-topic plus overall Math understanding

**Implementation**:
- **Database**: Added `sub_topic` field to AIInteraction model
- **Backend**: ProgressionAnalyzer methods for sub-topic and composite calculations
- **API Endpoints**:
  - `/progression-data/<class_id>/<sub_topic>`: Topic-specific progression
  - `/progression-data/<class_id>/composite`: Overall Math progression
- **Frontend**: Teacher dashboard with tabbed interface (Overall Math, Algebra, Statistics, Calculus)
- **Visualization**: Chart.js line charts with dark theme, showing 60-day progression

**Example Scenario**:
Student has 90% mastery in Algebra (50 interactions) and starts Statistics with 60% (5 interactions):
- **Without adaptive weighting**: Composite = (90+60)/2 = 75% (immediate 15% drop!)
- **With adaptive weighting**: Composite = (90×1.0 + 60×0.5)/(1.0+0.5) = 80% (maintains context)

**Test Data**: 999 AI interactions generated across 3 students over 60 days, distributed: Algebra (405), Statistics (317), Calculus (277)

**Recent Fixes (October 2025)**:
- **Sigmoid Learning Curve**: Fixed calculation to properly map time-based progression (0→1) to mastery curves, eliminating flat progression lines
- **Unified Score Calculation**: Improvement metrics now use same database-driven calculation as graphs (average of first 5 interactions for start, last 10 for current)
- **Interval-Based Grouping**: All tabs use consistent 3-day interval aggregation instead of noisy day-by-day data points
- **Graph-Card Alignment**: Graphs and improvement cards now show matching numbers (Alex: 50.5%→89.5%, Jordan: 36.8%→77.5%, Taylor: 25.7%→56.7%)

### AxonAI Demo Features (December 2025)

**P0: Subject Scope Lock**
- `_is_in_scope()` pre-OpenAI gate blocks off-topic requests BEFORE calling AI
- Subject keyword mapping for Math, Science, English, History, and general education
- Policy enforcement for non-educational content (recipes, dating, violence, etc.)
- Returns `blocked=true` with `blocked_reason` explaining why request was rejected

**P0: Enhanced API Responses**
- `/api/chat` and `/api/tutor/chat` now include `blocked`, `blocked_reason`, `subject` fields
- `get_chat_history()` returns JSON-safe dicts with ISO timestamps
- Persistent quick check counter via `OptimizedProfile.chat_counters` JSON field

**P1: Content-Aware RAG Retrieval**
- `retrieve_relevant_content()` extracts text from PDFs using pypdf
- TF-IDF keyword ranking for relevance scoring
- Returns top-3 snippets within token budget for inclusion in prompts

**P2: TutoringPlan Metadata**
- `/api/tutor/chat` includes `plan` object with:
  - `strategy`: Teaching strategy being used (quick_check, scaffolding, etc.)
  - `sub_topic`: Current skill focus (algebra, geometry, etc.)
  - `difficulty`: Adaptive difficulty level (easy, medium, hard)
  - `blocked`: Whether request was scope-blocked

**Smoke Test**: Run `python scripts/smoke_demo.py` to verify all features

### P3/P4/P5 Features (December 2025)

**P3: Epsilon-Greedy Strategy Selection**
- Bandit learning replaces simple strategy selection
- Success tracking per (user, skill, strategy) with wins/trials
- Epsilon=0.15 exploration, cold-start defaults by subject
- Weights: quick_check=1.0, quiz=1.5; success threshold=70%

**P3: Misconception Diagnosis**
- `diagnose_misconception()` analyzes incorrect answers
- Returns structured JSON: misconception_tags, reasoning_gap, next_step_recommendation, micro_lesson, followup_check
- Stored on AIInteraction records for learning analytics
- Remediation payload returned to frontend on wrong answers

**P4: Teacher Usefulness Endpoints**
- `GET /api/teacher/heatmap/<class_id>`: Class skill averages, top 5 misconceptions (30 days), students needing attention (mastery<70)
- `GET /api/teacher/student/<student_id>/<class_id>/misconceptions`: Timeline, summary, recommended interventions

**P5: Production Hardening**
- Rate limiting: 30 requests/5 minutes per user on tutor endpoints
- CSRF protection for POST endpoints (form submissions)
- Database-backed rate limit storage for persistence

**Canonical Skill Taxonomy**
- Math: algebra, geometry, arithmetic, statistics, functions, calculus, general
- English: grammar, writing, reading_comprehension, vocabulary, literature, general
- Science: biology, chemistry, physics, earth_science, scientific_method, general
- History: ancient, medieval, modern, civics, geography, source_analysis, general

**Migration SQL**
```sql
ALTER TABLE ai_interaction ADD COLUMN IF NOT EXISTS misconception_tags TEXT;
ALTER TABLE ai_interaction ADD COLUMN IF NOT EXISTS reasoning_gap TEXT;
ALTER TABLE ai_interaction ADD COLUMN IF NOT EXISTS next_step_recommendation TEXT;
ALTER TABLE optimized_profile ADD COLUMN IF NOT EXISTS strategy_success_rates TEXT;
CREATE TABLE IF NOT EXISTS rate_limit_entry (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, endpoint VARCHAR(100) NOT NULL, request_count INTEGER DEFAULT 1, window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
```

### Adaptive ML Architecture (December 2025)

**Overview**: ML models are hosted on an external Render service. This Flask app calls the ML API via HTTP for mastery, risk, and bandit predictions.

**Architecture Refactoring (December 18, 2025)**:
- Local ML code moved to `deprecated_local_ml/` (mastery_model, risk_model, bandit, retrieval, training)
- New `services/ml_api_client.py` - HTTP client for external ML services
- All ML inference now routes through external API when `ML_API_BASE_URL` is configured
- Database connection updated to support Supabase PostgreSQL with pooler URL and SSL

**Environment Variables**:
- `SUPABASE_DB_URL` or `DATABASE_URL`: PostgreSQL connection string (pooler URL preferred for IPv4 compatibility)
- `ML_API_BASE_URL`: Base URL for Render-hosted ML service (e.g., `https://your-ml-service.onrender.com`)
- `AXON_SERVICE_KEY`: Shared secret for ML API authentication (sent as X-AXON-KEY header)
- `USE_LOCAL_ML`: Set to "true" to use deprecated local ML (default: false)
- `USE_LOCAL_SQLITE_AGENTS`: Set to "true" to enable SQLite-based agents (default: false)
- `ENABLE_SCHEDULER`: Set to "false" to disable background scheduler (default: true)

**ML API Endpoints** (called from services/ml_api_client.py):
- `POST /mastery/predict`: Predict mastery for (student_id, skill, class_id)
- `POST /risk/score`: Score risk for (student_id, class_id)
- `POST /bandit/select`: Select strategy for (student_id, class_id, bandit_type)
- `POST /bandit/update`: Update bandit reward after interaction
- `POST /mastery/train` and `/risk/train`: Trigger retraining (admin only)

**Smoke Test**:
```bash
python scripts/smoke_ml_api.py
```

**Deprecated Local ML Components** (in deprecated_local_ml/):
- `mastery_model/`: Logistic regression for mastery prediction
- `risk_model/`: Logistic regression for at-risk prediction
- `bandit/`: LinUCB contextual bandit
- `retrieval/`: Embedding-based RAG
- `training/`: Training pipeline scripts

**Database Models** (still active in models.py):
- `MasteryState`: Cached mastery state per (student, skill) pair
- `RiskScore`: Cached at-risk prediction per (student, class) pair
- `BanditPolicyState`: Bandit policy state per (student, class) pair
- `ContentEmbedding`: Embeddings for content retrieval
- `ModelVersion`: Track ML model versions and metrics

**Feature Flags** (app.py and services/ml_integration.py):
- Remote ML API is used by default when `ML_API_BASE_URL` is configured
- Falls back to database-cached values when API is unavailable
- Falls back to heuristics when no data available

**Demo Data Generation**:
```bash
python scripts/simulate_school.py --students 100 --days 30 --classes 3 --seed 42
```

**Documentation**: See `docs/ADAPTIVE_ML_ARCHITECTURE.md` and `docs/SIMULATOR_GUIDE.md`

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM integration
- **bcrypt**: Password hashing
- **SQLAlchemy**: Database abstraction layer

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework
- **Font Awesome 6**: Icon library
- **Bootstrap JavaScript**: Interactive components

### AI Providers
- **OpenAI**: GPT-4o
- **AWS**: Custom-hosted models
- **Local**: Ollama/local models