# School Management System

## Overview

This is a Flask-based school management system that provides role-based access control for administrators, teachers, and students. The application uses SQLAlchemy with SQLite for data persistence and implements session-based authentication with bcrypt password hashing.

## User Preferences

Preferred communication style: Simple, everyday language.

Design preferences: Grayscale color scheme, flat 2D design with depth (like 2D games), no rounded buttons, everything angular and geometric.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework
- **Database ORM**: SQLAlchemy with declarative base model
- **Database**: PostgreSQL 17 (production-ready database with connection pooling)
- **Authentication**: Session-based with bcrypt password hashing
- **Authorization**: Role-based access control (admin, teacher, student)

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **Client-side**: Vanilla JavaScript with Bootstrap components

### Security Architecture
- **Password Security**: bcrypt hashing with salt
- **Session Management**: Flask sessions with secret key
- **Access Control**: Decorator-based role authorization
- **Input Validation**: Server-side form validation

## Key Components

### Authentication & Authorization (`auth.py`)
- **Password Management**: bcrypt hashing and verification
- **Access Decorators**: `@login_required`, `@admin_required`, `@role_required`
- **Session Security**: User session management with role-based access

### Data Models (`models.py`)
- **User Model**: Core user entity with roles (admin, teacher, student)
- **User Properties**: Email, password hash, role, names, timestamps, active status
- **Helper Methods**: Full name generation and dictionary serialization

### Application Routes (`routes.py`)
- **Authentication Routes**: Login/logout with role-based redirection
- **Dashboard Routes**: Role-specific dashboard rendering
- **User Management**: Admin-only user CRUD operations (partial implementation)

### Database Initialization (`init_db.py`)
- **Dummy Data**: Creates default users for each role during startup
- **Safe Initialization**: Checks for existing users to prevent duplicates

## Data Flow

### Authentication Flow
1. User selects role type (admin/teacher/student) on login page
2. Email and password validation against role-specific user records
3. Session establishment with user ID, role, and name
4. Role-based dashboard redirection

### Authorization Flow
1. Route decorators check session for user authentication
2. Role verification against database for sensitive operations
3. Flash messages for unauthorized access attempts
4. Graceful redirection to appropriate pages

### User Management Flow (Admin)
1. Admin accesses user management interface
2. CRUD operations on user accounts
3. Role assignment and status management
4. Real-time user statistics display

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM integration
- **bcrypt**: Password hashing and verification
- **SQLAlchemy**: Database abstraction layer

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library
- **Bootstrap JavaScript**: Interactive components

## Deployment Strategy

### Development Configuration
- **Database**: SQLite file-based storage
- **Debug Mode**: Enabled for development
- **Secret Key**: Environment variable with fallback
- **Host/Port**: 0.0.0.0:5000 for container compatibility

### Production Considerations
- **Database**: Configurable URI for PostgreSQL/MySQL
- **Secret Key**: Must be set via environment variable
- **Debug Mode**: Should be disabled
- **HTTPS**: SSL termination at load balancer/proxy level

### File Structure
```
├── app.py              # Application factory and configuration
├── main.py             # Application entry point
├── models.py           # Database models
├── routes.py           # URL routing and view functions
├── auth.py             # Authentication and authorization utilities
├── init_db.py          # Database initialization and dummy data
├── static/
│   └── style.css       # Custom CSS styles
└── templates/          # Jinja2 HTML templates
    ├── base.html       # Base template with navigation
    ├── login.html      # Authentication page
    ├── *_dashboard.html # Role-specific dashboards
    ├── manage_users.html # Admin user management
    └── edit_user.html  # User creation/editing form
```

### Database Schema
- **Users Table**: id, email, password_hash, role, first_name, last_name, created_at, is_active
- **Classes Table**: id, name, description, teacher_id, created_at, is_active
- **Assignments Table**: id, title, description, class_id, due_date, max_points, created_at, is_active
- **Assignment Submissions Table**: id, assignment_id, student_id, content, file_path, submitted_at
- **Grades Table**: id, assignment_id, student_id, submission_id, grade, feedback, graded_at, graded_by
- **Content Files Table**: id, class_id, name, file_path, file_type, uploaded_by, uploaded_at
- **Class Users Table**: Many-to-many relationship table for class enrollment

### Recent Changes (January 2025)
- **Database Migration**: Successfully migrated from SQLite to PostgreSQL for production readiness
- **Complete Feature Set**: Full school management functionality implemented with role-based access control
- **Architecture Optimization**: Chose enhanced Flask templates over complex React setup for better maintainability
- **AI Integration Success**: Fully functional AI tutoring system with multi-provider support (OpenAI, AWS, local)
- **Enhanced Admin Dashboard**: Advanced data export with column/row selection and relationship visualization
- **Interactive Export System**: Real-time table selection with visual relationship mapping and statistics
- **Student AI Tutor**: Subject-specific chatbots (Math, Science, English, History) with personalized responses
- **AI Analytics Dashboard**: Comprehensive admin insights into student engagement and AI performance
- **Bootstrap Integration**: Enhanced Flask templates with Bootstrap 5 dark theme and FontAwesome icons
- **Local Model Support**: Complete Ollama integration guide with subject-specific model recommendations
- **Comprehensive Documentation**: Detailed README with database relationships, setup guides, and troubleshooting
- **Production Ready**: Enhanced with connection pooling, security features, and deployment documentation
- **Windows Compatibility**: Added Windows-specific setup instructions with PowerShell commands
- **Cross-Platform Support**: Created requirements-windows.txt and WINDOWS_SETUP.md for Windows users
- **Enhanced Troubleshooting**: Platform-specific troubleshooting guides for Windows, Linux, and macOS
- **PostgreSQL 17 Support**: Updated all configuration and setup instructions for PostgreSQL version 17

### AI Enhancement Features (January 2025)
- **Multi-Provider Support**: Configurable AI providers (OpenAI GPT-4o, AWS-hosted models, local Ollama)
- **Subject-Specific Tutors**: Fine-tuned AI models for mathematics, science, English, history, and art
- **Personalized Learning**: AI responses based on student learning style, grade performance, and academic goals
- **Chat History Storage**: Complete conversation tracking with context preservation for AI training
- **Student Profiles**: Extended profiles with learning preferences, study patterns, and performance metrics
- **Teacher Insights**: AI-generated analytics about student engagement and learning patterns
- **Demo Mode**: Intelligent fallback responses when AI services are unavailable
- **Configuration System**: Simple variable switching between AI providers with comprehensive setup instructions

### Data Management Features
- **Advanced Export System**: Selective data export with relationship visualization
- **Export Tree Preview**: Interactive preview showing exact data structure and record counts
- **CSV Generation**: Comprehensive data export including users, classes, chat history, and AI interactions
- **Admin Dashboard Integration**: Seamless access to data export tools with modal interface
- **Real-time Statistics**: Live dashboard stats including AI chat interactions and model usage

### Technology Stack Update
- **Frontend**: React 19.1.0, React Router, React-Bootstrap, FontAwesome
- **Backend API**: Flask RESTful API endpoints with AI integration
- **AI Integration**: OpenAI GPT-4o, requests library for custom endpoints, multi-provider architecture
- **Database**: PostgreSQL with extended schema for AI features (ChatMessage, AIModel, StudentProfile)
- **Styling**: Bootstrap 5 dark theme, responsive design, custom CSS
- **Authentication**: Session-based auth with bcrypt, JWT token support
- **File Handling**: Multi-format upload support with progress indicators
- **Configuration**: Environment-based AI provider switching with validation

### AI Configuration Guide
To switch between AI providers, modify the `AI_PROVIDER` environment variable or update `ai_config.py`:
- **OpenAI**: Set `AI_PROVIDER=openai` and provide `OPENAI_API_KEY`
- **AWS Hosted**: Set `AI_PROVIDER=aws` and configure `AWS_AI_ENDPOINT` and `AWS_AI_API_KEY`
- **Local Models**: Set `AI_PROVIDER=local` and configure `LOCAL_AI_ENDPOINT` (default: Ollama)
- **Demo Mode**: Automatically activated when no AI service is available

The application now provides intelligent, personalized AI tutoring integrated seamlessly with the school management system.