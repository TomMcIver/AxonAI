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