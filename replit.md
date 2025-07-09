# School Management System

## Overview

This is a Flask-based school management system that provides role-based access control for administrators, teachers, and students. The application uses SQLAlchemy with SQLite for data persistence and implements session-based authentication with bcrypt password hashing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework
- **Database ORM**: SQLAlchemy with declarative base model
- **Database**: PostgreSQL (production-ready database with connection pooling)
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
- **Class Management**: Admin can create and manage classes, assign teachers
- **Assignment System**: Teachers can create assignments, students can submit, teachers can grade
- **Enrollment System**: Many-to-many relationships between students and classes
- **File Upload System**: Complete file upload functionality for PDFs, docs, presentations, images
- **Teacher Tools Fixed**: All teacher dashboard buttons (Students, Gradebook, Course Content) working properly
- **Template Errors Resolved**: Fixed all Jinja2 template calculation errors and data structure issues
- **Comprehensive Test Data**: Added realistic assignments, submissions, grades, and content files

The application follows a traditional MVC pattern with clear separation of concerns and implements security best practices for educational institution management.