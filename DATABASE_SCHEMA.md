# 📊 Database Schema Documentation

## Overview

The School Management System uses a PostgreSQL 17 database with a comprehensive relational schema designed for educational data management and AI integration.

## 🏗️ Entity Relationship Diagram

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                        USERS                                │
                    │ ┌─────────────────────────────────────────────────────────┐ │
                    │ │ id (PK)               │ email (UNIQUE)                  │ │
                    │ │ password_hash         │ role (admin/teacher/student)    │ │
                    │ │ first_name            │ last_name                       │ │
                    │ │ photo_url             │ created_at                      │ │
                    │ │ is_active             │ age                             │ │
                    │ │ learning_style        │ interests (JSON)                │ │
                    │ │ academic_goals        │ preferred_difficulty            │ │
                    │ └─────────────────────────────────────────────────────────┘ │
                    └─────────────────┬───────────────────────┬───────────────────┘
                                      │                       │
                         ┌────────────┴─────────────┐        │
                         │ (teacher_id)             │        │ (user_id)
                         ▼                          │        ▼
        ┌──────────────────────────────────┐        │   ┌─────────────────────────────┐
        │            CLASSES               │        │   │      STUDENT_PROFILES       │
        │ ┌──────────────────────────────┐ │        │   │ ┌─────────────────────────┐ │
        │ │ id (PK)                      │ │        │   │ │ id (PK)                 │ │
        │ │ name                         │ │        │   │ │ user_id (FK → users.id) │ │
        │ │ description                  │ │        │   │ │ learning_preferences    │ │
        │ │ subject                      │ │        │   │ │ study_patterns          │ │
        │ │ teacher_id (FK → users.id)   │ │        │   │ │ performance_metrics     │ │
        │ │ ai_model_id (FK)             │ │        │   │ │ ai_interaction_history  │ │
        │ │ created_at                   │ │        │   │ │ last_updated            │ │
        │ │ is_active                    │ │        │   │ └─────────────────────────┘ │
        │ └──────────────────────────────┘ │        │   └─────────────────────────────┘
        └─────────────┬────────────────────┘        │
                      │                             │
                      │ (class_id)                  │
                      ▼                             │
        ┌──────────────────────────────────┐        │
        │          ASSIGNMENTS             │        │
        │ ┌──────────────────────────────┐ │        │
        │ │ id (PK)                      │ │        │
        │ │ title                        │ │        │
        │ │ description                  │ │        │
        │ │ class_id (FK → classes.id)   │ │        │
        │ │ due_date                     │ │        │
        │ │ max_points                   │ │        │
        │ │ created_at                   │ │        │
        │ │ is_active                    │ │        │
        │ └──────────────────────────────┘ │        │
        └─────────────┬────────────────────┘        │
                      │                             │
                      │ (assignment_id)             │
                      ▼                             │
        ┌──────────────────────────────────┐        │
        │     ASSIGNMENT_SUBMISSIONS       │        │
        │ ┌──────────────────────────────┐ │        │
        │ │ id (PK)                      │ │        │
        │ │ assignment_id (FK)           │ │        │
        │ │ student_id (FK → users.id)   │ │◄───────┘
        │ │ content                      │ │
        │ │ file_path                    │ │
        │ │ file_name                    │ │
        │ │ submitted_at                 │ │
        │ └──────────────────────────────┘ │
        └─────────────┬────────────────────┘
                      │
                      │ (submission_id)
                      ▼
        ┌──────────────────────────────────┐
        │             GRADES               │
        │ ┌──────────────────────────────┐ │
        │ │ id (PK)                      │ │
        │ │ assignment_id (FK)           │ │
        │ │ student_id (FK → users.id)   │ │
        │ │ submission_id (FK)           │ │
        │ │ grade                        │ │
        │ │ feedback                     │ │
        │ │ graded_at                    │ │
        │ │ graded_by (FK → users.id)    │ │
        │ └──────────────────────────────┘ │
        └──────────────────────────────────┘


                    ┌─────────────────────────────────────────────────────────────┐
                    │                      AI_MODELS                             │
                    │ ┌─────────────────────────────────────────────────────────┐ │
                    │ │ id (PK)               │ subject                         │ │
                    │ │ model_name            │ fine_tuned_id                   │ │
                    │ │ prompt_template       │ max_tokens                      │ │
                    │ │ temperature           │ is_active                       │ │
                    │ │ created_at            │                                 │ │
                    │ └─────────────────────────────────────────────────────────┘ │
                    └─────────────────┬───────────────────────────────────────────┘
                                      │
                                      │ (ai_model_id)
                                      ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                   CHAT_MESSAGES                            │
                    │ ┌─────────────────────────────────────────────────────────┐ │
                    │ │ id (PK)               │ user_id (FK → users.id)         │ │
                    │ │ class_id (FK)         │ ai_model_id (FK)                │ │
                    │ │ message               │ response                        │ │
                    │ │ message_type          │ context_data (JSON)             │ │
                    │ │ created_at            │                                 │ │
                    │ └─────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────┘


                    ┌─────────────────────────────────────────────────────────────┐
                    │                   CONTENT_FILES                            │
                    │ ┌─────────────────────────────────────────────────────────┐ │
                    │ │ id (PK)               │ class_id (FK → classes.id)      │ │
                    │ │ name                  │ file_path                       │ │
                    │ │ file_type             │ uploaded_by (FK → users.id)     │ │
                    │ │ uploaded_at           │                                 │ │
                    │ └─────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────┘


                    ┌─────────────────────────────────────────────────────────────┐
                    │                    CLASS_USERS                             │
                    │           (Many-to-Many Relationship Table)                │
                    │ ┌─────────────────────────────────────────────────────────┐ │
                    │ │ class_id (FK → classes.id)                              │ │
                    │ │ user_id (FK → users.id)                                 │ │
                    │ │ enrolled_at                                             │ │
                    │ │ is_active                                               │ │
                    │ └─────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────┘
```

## 📋 Table Specifications

### 👥 Users Table
**Purpose**: Central user management for all system roles
**Type**: Core Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique user identifier |
| `email` | `VARCHAR(120)` | `UNIQUE, NOT NULL` | User login email |
| `password_hash` | `VARCHAR(256)` | `NOT NULL` | Bcrypt hashed password |
| `role` | `VARCHAR(20)` | `NOT NULL` | admin/teacher/student |
| `first_name` | `VARCHAR(50)` | `NOT NULL` | User's first name |
| `last_name` | `VARCHAR(50)` | `NOT NULL` | User's last name |
| `photo_url` | `VARCHAR(200)` | `NULLABLE` | Profile picture URL |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Account creation time |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Account status |
| `age` | `INTEGER` | `NULLABLE` | Student age (student only) |
| `learning_style` | `VARCHAR(50)` | `NULLABLE` | visual/auditory/kinesthetic/reading |
| `interests` | `TEXT` | `NULLABLE` | JSON array of interests |
| `academic_goals` | `TEXT` | `NULLABLE` | Student academic goals |
| `preferred_difficulty` | `VARCHAR(20)` | `NULLABLE` | beginner/intermediate/advanced |

**Relationships**:
- One-to-Many → `classes` (as teacher)
- Many-to-Many → `classes` (as student via `class_users`)
- One-to-Many → `assignment_submissions`
- One-to-Many → `grades` (as student)
- One-to-Many → `grades` (as grader)
- One-to-Many → `chat_messages`
- One-to-One → `student_profile`

### 🏫 Classes Table
**Purpose**: Course/class management
**Type**: Core Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique class identifier |
| `name` | `VARCHAR(100)` | `NOT NULL` | Class name |
| `description` | `TEXT` | `NULLABLE` | Class description |
| `subject` | `VARCHAR(50)` | `NULLABLE` | Subject category |
| `teacher_id` | `INTEGER` | `FK → users.id` | Assigned teacher |
| `ai_model_id` | `INTEGER` | `FK → ai_models.id` | Associated AI model |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Class creation time |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Class status |

**Relationships**:
- Many-to-One ← `users` (teacher)
- Many-to-One ← `ai_models`
- One-to-Many → `assignments`
- One-to-Many → `content_files`
- One-to-Many → `chat_messages`
- Many-to-Many → `users` (students via `class_users`)

### 📝 Assignments Table
**Purpose**: Assignment/homework management
**Type**: Academic Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique assignment identifier |
| `title` | `VARCHAR(200)` | `NOT NULL` | Assignment title |
| `description` | `TEXT` | `NULLABLE` | Assignment instructions |
| `class_id` | `INTEGER` | `FK → classes.id` | Parent class |
| `due_date` | `TIMESTAMP` | `NULLABLE` | Submission deadline |
| `max_points` | `INTEGER` | `DEFAULT 100` | Maximum possible points |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Assignment creation time |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Assignment status |

**Relationships**:
- Many-to-One ← `classes`
- One-to-Many → `assignment_submissions`
- One-to-Many → `grades`

### 📤 Assignment Submissions Table
**Purpose**: Student work submissions
**Type**: Academic Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique submission identifier |
| `assignment_id` | `INTEGER` | `FK → assignments.id` | Target assignment |
| `student_id` | `INTEGER` | `FK → users.id` | Submitting student |
| `content` | `TEXT` | `NULLABLE` | Text submission content |
| `file_path` | `VARCHAR(200)` | `NULLABLE` | Uploaded file path |
| `file_name` | `VARCHAR(200)` | `NULLABLE` | Original filename |
| `submitted_at` | `TIMESTAMP` | `DEFAULT NOW()` | Submission time |

**Relationships**:
- Many-to-One ← `assignments`
- Many-to-One ← `users` (student)
- One-to-One → `grades`

### ⭐ Grades Table
**Purpose**: Grade tracking and feedback
**Type**: Academic Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique grade identifier |
| `assignment_id` | `INTEGER` | `FK → assignments.id` | Graded assignment |
| `student_id` | `INTEGER` | `FK → users.id` | Student receiving grade |
| `submission_id` | `INTEGER` | `FK → submissions.id` | Associated submission |
| `grade` | `FLOAT` | `NULLABLE` | Numerical grade |
| `feedback` | `TEXT` | `NULLABLE` | Teacher feedback |
| `graded_at` | `TIMESTAMP` | `DEFAULT NOW()` | Grading time |
| `graded_by` | `INTEGER` | `FK → users.id` | Grading teacher |

**Relationships**:
- Many-to-One ← `assignments`
- Many-to-One ← `users` (student)
- Many-to-One ← `users` (teacher)
- One-to-One ← `assignment_submissions`

### 🤖 AI Models Table
**Purpose**: AI model configuration and management
**Type**: AI Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique model identifier |
| `subject` | `VARCHAR(100)` | `NOT NULL` | Subject specialization |
| `model_name` | `VARCHAR(200)` | `NOT NULL` | Model identifier/name |
| `fine_tuned_id` | `VARCHAR(200)` | `NULLABLE` | Fine-tuned model ID |
| `prompt_template` | `TEXT` | `NULLABLE` | System prompt template |
| `max_tokens` | `INTEGER` | `DEFAULT 1000` | Response length limit |
| `temperature` | `FLOAT` | `DEFAULT 0.7` | Response creativity (0-1) |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Model availability |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Model registration time |

**Relationships**:
- One-to-Many → `classes`
- One-to-Many → `chat_messages`

### 💬 Chat Messages Table
**Purpose**: AI conversation history and context
**Type**: AI Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique message identifier |
| `user_id` | `INTEGER` | `FK → users.id` | Message author |
| `class_id` | `INTEGER` | `FK → classes.id` | Conversation context |
| `ai_model_id` | `INTEGER` | `FK → ai_models.id` | AI model used |
| `message` | `TEXT` | `NOT NULL` | User's message |
| `response` | `TEXT` | `NOT NULL` | AI's response |
| `message_type` | `VARCHAR(20)` | `NOT NULL` | student/teacher/system |
| `context_data` | `TEXT` | `NULLABLE` | JSON context data |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Conversation time |

**Relationships**:
- Many-to-One ← `users`
- Many-to-One ← `classes`
- Many-to-One ← `ai_models`

### 👤 Student Profiles Table
**Purpose**: Extended student information for AI personalization
**Type**: AI Enhancement Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique profile identifier |
| `user_id` | `INTEGER` | `FK → users.id, UNIQUE` | Associated student |
| `learning_preferences` | `TEXT` | `NULLABLE` | JSON learning preferences |
| `study_patterns` | `TEXT` | `NULLABLE` | JSON study behavior data |
| `performance_metrics` | `TEXT` | `NULLABLE` | JSON performance analytics |
| `ai_interaction_history` | `TEXT` | `NULLABLE` | JSON AI interaction summary |
| `last_updated` | `TIMESTAMP` | `DEFAULT NOW()` | Profile update time |

**Relationships**:
- One-to-One ← `users` (students only)

### 📁 Content Files Table
**Purpose**: Course material and file management
**Type**: Content Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique file identifier |
| `class_id` | `INTEGER` | `FK → classes.id` | Associated class |
| `name` | `VARCHAR(200)` | `NOT NULL` | Display filename |
| `file_path` | `VARCHAR(200)` | `NOT NULL` | Storage file path |
| `file_type` | `VARCHAR(50)` | `NOT NULL` | pdf/txt/slides/image |
| `uploaded_by` | `INTEGER` | `FK → users.id` | Uploader (teacher) |
| `uploaded_at` | `TIMESTAMP` | `DEFAULT NOW()` | Upload time |

**Relationships**:
- Many-to-One ← `classes`
- Many-to-One ← `users` (uploader)

### 🔗 Class Users Table (Junction)
**Purpose**: Many-to-many relationship between classes and students
**Type**: Relationship Entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `class_id` | `INTEGER` | `FK → classes.id` | Class reference |
| `user_id` | `INTEGER` | `FK → users.id` | Student reference |
| `enrolled_at` | `TIMESTAMP` | `DEFAULT NOW()` | Enrollment time |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Enrollment status |

**Constraints**: 
- `PRIMARY KEY (class_id, user_id)`
- `CHECK (user.role = 'student')`

**Relationships**:
- Many-to-One ← `classes`
- Many-to-One ← `users` (students only)

## 🔄 Relationship Analysis

### Primary Relationships

#### User-Centric Relationships
```sql
-- A user can be a teacher of multiple classes
users (1) ←→ (N) classes [teacher_id]

-- A user (student) can enroll in multiple classes
users (N) ←→ (N) classes [via class_users]

-- A user (student) can submit multiple assignments
users (1) ←→ (N) assignment_submissions [student_id]

-- A user (student) can receive multiple grades
users (1) ←→ (N) grades [student_id]

-- A user (teacher) can grade multiple assignments
users (1) ←→ (N) grades [graded_by]

-- A user can have multiple AI conversations
users (1) ←→ (N) chat_messages [user_id]

-- A student user has one extended profile
users (1) ←→ (1) student_profiles [user_id]
```

#### Class-Centric Relationships
```sql
-- A class has multiple assignments
classes (1) ←→ (N) assignments [class_id]

-- A class has multiple content files
classes (1) ←→ (N) content_files [class_id]

-- A class has multiple AI conversations
classes (1) ←→ (N) chat_messages [class_id]

-- A class uses one AI model
classes (N) ←→ (1) ai_models [ai_model_id]
```

#### Assignment Flow Relationships
```sql
-- An assignment has multiple submissions
assignments (1) ←→ (N) assignment_submissions [assignment_id]

-- An assignment has multiple grades
assignments (1) ←→ (N) grades [assignment_id]

-- A submission has one grade
assignment_submissions (1) ←→ (1) grades [submission_id]
```

#### AI System Relationships
```sql
-- An AI model is used in multiple classes
ai_models (1) ←→ (N) classes [ai_model_id]

-- An AI model handles multiple conversations
ai_models (1) ←→ (N) chat_messages [ai_model_id]
```

### Referential Integrity Rules

#### Cascade Behaviors
```sql
-- When a user is deleted
ON DELETE CASCADE:
- assignment_submissions (student submissions)
- chat_messages (user conversations)
- student_profiles (extended profiles)

ON DELETE SET NULL:
- classes (teacher assignments)
- grades (graded_by references)

-- When a class is deleted
ON DELETE CASCADE:
- assignments (class assignments)
- content_files (class materials)
- chat_messages (class conversations)
- class_users (enrollments)

-- When an assignment is deleted
ON DELETE CASCADE:
- assignment_submissions (submissions)
- grades (assignment grades)

-- When an AI model is deleted
ON DELETE SET NULL:
- classes (ai_model_id)
- chat_messages (ai_model_id)
```

## 📊 Data Export Relationships

When exporting data through the admin interface, the following relationships are preserved:

### Export Structure
```
users.csv
├── Contains: id, email, role, names, learning_data
├── Links to: classes (via class_users), submissions, grades, chat_messages

classes.csv
├── Contains: id, name, subject, teacher_id, ai_model_id
├── Links to: users (teacher), ai_models, assignments, content_files

assignments.csv
├── Contains: id, title, class_id, due_date, max_points
├── Links to: classes, submissions, grades

assignment_submissions.csv
├── Contains: id, assignment_id, student_id, content, file_info
├── Links to: assignments, users (students), grades

grades.csv
├── Contains: id, assignment_id, student_id, grade, feedback
├── Links to: assignments, users (student & teacher), submissions

chat_messages.csv
├── Contains: id, user_id, class_id, ai_model_id, conversation_data
├── Links to: users, classes, ai_models

ai_models.csv
├── Contains: id, subject, model_name, configuration
├── Links to: classes, chat_messages

student_profiles.csv (optional)
├── Contains: id, user_id, learning_preferences, performance_data
├── Links to: users (students only)

content_files.csv (optional)
├── Contains: id, class_id, file_info, uploaded_by
├── Links to: classes, users (uploaders)
```

### Foreign Key Preservation

All exported CSV files maintain foreign key relationships through ID references:

- `teacher_id` in classes.csv references `id` in users.csv
- `student_id` in submissions.csv references `id` in users.csv
- `class_id` in assignments.csv references `id` in classes.csv
- `assignment_id` in grades.csv references `id` in assignments.csv

This structure allows for complete data reconstruction and relationship analysis in external tools.

## 🔍 Query Optimization

### Recommended Indexes

```sql
-- User queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Class queries
CREATE INDEX idx_classes_teacher ON classes(teacher_id);
CREATE INDEX idx_classes_subject ON classes(subject);
CREATE INDEX idx_classes_active ON classes(is_active);

-- Assignment queries
CREATE INDEX idx_assignments_class ON assignments(class_id);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);

-- Submission queries
CREATE INDEX idx_submissions_assignment ON assignment_submissions(assignment_id);
CREATE INDEX idx_submissions_student ON assignment_submissions(student_id);
CREATE INDEX idx_submissions_date ON assignment_submissions(submitted_at);

-- Grade queries
CREATE INDEX idx_grades_assignment ON grades(assignment_id);
CREATE INDEX idx_grades_student ON grades(student_id);
CREATE INDEX idx_grades_teacher ON grades(graded_by);

-- Chat queries
CREATE INDEX idx_chat_user ON chat_messages(user_id);
CREATE INDEX idx_chat_class ON chat_messages(class_id);
CREATE INDEX idx_chat_date ON chat_messages(created_at);

-- AI model queries
CREATE INDEX idx_ai_models_subject ON ai_models(subject);
CREATE INDEX idx_ai_models_active ON ai_models(is_active);

-- Class enrollment queries
CREATE INDEX idx_class_users_class ON class_users(class_id);
CREATE INDEX idx_class_users_user ON class_users(user_id);
```

### Common Query Patterns

#### Student Dashboard Queries
```sql
-- Get student's enrolled classes
SELECT c.* FROM classes c
JOIN class_users cu ON c.id = cu.class_id
WHERE cu.user_id = ? AND cu.is_active = true;

-- Get student's pending assignments
SELECT a.* FROM assignments a
JOIN class_users cu ON a.class_id = cu.class_id
LEFT JOIN assignment_submissions s ON a.id = s.assignment_id AND s.student_id = ?
WHERE cu.user_id = ? AND s.id IS NULL AND a.due_date > NOW();

-- Get student's recent grades
SELECT g.*, a.title as assignment_title FROM grades g
JOIN assignments a ON g.assignment_id = a.id
WHERE g.student_id = ? ORDER BY g.graded_at DESC LIMIT 10;
```

#### Teacher Dashboard Queries
```sql
-- Get teacher's classes with student counts
SELECT c.*, COUNT(cu.user_id) as student_count FROM classes c
LEFT JOIN class_users cu ON c.id = cu.class_id AND cu.is_active = true
WHERE c.teacher_id = ? GROUP BY c.id;

-- Get ungraded submissions for teacher's classes
SELECT s.*, a.title, u.first_name, u.last_name FROM assignment_submissions s
JOIN assignments a ON s.assignment_id = a.id
JOIN classes c ON a.class_id = c.id
JOIN users u ON s.student_id = u.id
LEFT JOIN grades g ON s.id = g.submission_id
WHERE c.teacher_id = ? AND g.id IS NULL;
```

#### AI Analytics Queries
```sql
-- Get AI usage statistics by class
SELECT c.name, COUNT(cm.id) as message_count,
       COUNT(DISTINCT cm.user_id) as active_users
FROM classes c
LEFT JOIN chat_messages cm ON c.id = cm.class_id
WHERE cm.created_at > NOW() - INTERVAL '7 days'
GROUP BY c.id, c.name;

-- Get most active AI models
SELECT am.subject, am.model_name, COUNT(cm.id) as usage_count
FROM ai_models am
LEFT JOIN chat_messages cm ON am.id = cm.ai_model_id
GROUP BY am.id ORDER BY usage_count DESC;
```

## 🔧 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```sql
-- Clean old sessions (if using database sessions)
DELETE FROM sessions WHERE expires < NOW();

-- Update student profiles with recent activity
UPDATE student_profiles SET last_updated = NOW()
WHERE user_id IN (
    SELECT DISTINCT user_id FROM chat_messages 
    WHERE created_at > NOW() - INTERVAL '1 day'
);
```

#### Weekly Tasks
```sql
-- Archive old chat messages (optional)
INSERT INTO chat_messages_archive 
SELECT * FROM chat_messages 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Update performance metrics
-- (Custom business logic for calculating student performance)
```

#### Monthly Tasks
```sql
-- Analyze database performance
ANALYZE;

-- Reindex frequently used tables
REINDEX INDEX idx_chat_date;
REINDEX INDEX idx_submissions_date;

-- Archive completed assignments older than 1 year
UPDATE assignments SET is_active = false 
WHERE due_date < NOW() - INTERVAL '1 year';
```

### Backup Procedures

#### Full Database Backup
```bash
pg_dump -h localhost -U username -d school_management > backup_$(date +%Y%m%d).sql
```

#### Table-Specific Backups
```bash
# Export user data only
pg_dump -h localhost -U username -d school_management -t users > users_backup.sql

# Export AI conversation data
pg_dump -h localhost -U username -d school_management -t chat_messages > chat_backup.sql
```

#### Restore Procedures
```bash
# Full restore
psql -h localhost -U username -d school_management_new < backup_20250110.sql

# Selective restore
psql -h localhost -U username -d school_management < users_backup.sql
```

---

This database schema provides a robust foundation for educational data management with AI integration, ensuring data integrity, performance, and scalability for modern school management needs.