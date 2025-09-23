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