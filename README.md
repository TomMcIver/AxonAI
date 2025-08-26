# 🎓 TMC Learning - AI-Enhanced Learning Platform

A comprehensive Flask-based learning management web application with advanced AI tutoring capabilities, multi-provider AI support, and sophisticated data management tools.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Flask](https://img.shields.io/badge/flask-3.0+-red)
![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 🚀 Features

### 🎯 Core Management Features
- **Role-based Access Control**: Admin, Teacher, and Student roles with specific permissions
- **User Management**: Complete CRUD operations for all user types
- **Class Management**: Create, edit, and manage classes with teacher assignments
- **Assignment System**: Create assignments, track submissions, and grade work
- **Grade Management**: Comprehensive gradebook with performance analytics
- **Content Management**: File upload and sharing system for educational materials

### 🤖 AI-Enhanced Features
- **Multi-Provider AI Support**: OpenAI GPT-4o, AWS-hosted models, local Ollama integration
- **Subject-Specific AI Tutors**: Fine-tuned models for Mathematics, Science, English, History, and Art
- **Personalized Learning**: AI responses based on student profiles, learning styles, and academic performance
- **Chat History Storage**: Complete conversation tracking with context preservation
- **AI Analytics Dashboard**: Teacher insights into student engagement and learning patterns
- **Demo Mode**: Intelligent fallback responses when AI services are unavailable

### 📊 Advanced Data Management
- **Interactive Data Export**: Selective table and column export with relationship visualization
- **CSV Export System**: Comprehensive data export with ZIP packaging
- **Relationship Mapping**: Visual database relationship diagram in export interface
- **Real-time Statistics**: Live dashboard metrics including AI interaction data

## 🏗️ Architecture Overview

### Backend Architecture
- **Framework**: Flask 3.0+ with SQLAlchemy ORM
- **Database**: PostgreSQL with connection pooling and migrations
- **Authentication**: Session-based with bcrypt password hashing
- **AI Integration**: Multi-provider architecture supporting OpenAI, AWS, and local models
- **File Handling**: Secure upload system with multiple format support

### Frontend Architecture
- **Template Engine**: Enhanced Jinja2 templates with Bootstrap 5 dark theme
- **Interactive Components**: JavaScript-enhanced modals and forms
- **Responsive Design**: Mobile-first design with Bootstrap grid system
- **Icons**: Font Awesome 6.0 for consistent iconography

### Security Architecture
- **Password Security**: bcrypt hashing with secure salt generation
- **Session Management**: Flask sessions with configurable secret keys
- **Access Control**: Decorator-based role authorization
- **Input Validation**: Server-side form validation and sanitization
- **Database Security**: Parameterized queries and ORM protection

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 17 or higher
- Git for version control

## ⚡ Quick Start

Choose your operating system for specific instructions:

### 🖥️ Windows Setup

#### 1. Clone and Setup
```powershell
git clone <repository-url>
cd school-management-system
```

#### 2. Install Python Dependencies
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements-windows.txt
```

#### 3. Install PostgreSQL
Download and install PostgreSQL 17 from [postgresql.org](https://www.postgresql.org/download/windows/)

During installation:
- Set password for 'postgres' user
- Note the port (default: 5432)
- Install pgAdmin 4 (recommended)

#### 4. Create Database (Windows)
```powershell
# Open Command Prompt as Administrator
# Navigate to PostgreSQL bin directory
cd "C:\Program Files\PostgreSQL\17\bin"

# Create database and user
.\createdb.exe -U postgres school_management
.\createuser.exe -U postgres -P your_username

# Connect to PostgreSQL and grant privileges
.\psql.exe -U postgres
```

In PostgreSQL shell:
```sql
GRANT ALL PRIVILEGES ON DATABASE school_management TO your_username;
\q
```

#### 5. Environment Configuration (Windows)
Create a `.env` file in the root directory:
```env
# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/school_management
PGHOST=localhost
PGPORT=5432
PGUSER=your_username
PGPASSWORD=your_password
PGDATABASE=school_management

# Security
SESSION_SECRET=your-super-secret-key-here

# AI Provider Configuration (choose one)
AI_PROVIDER=openai  # Options: openai, aws, local, demo

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# AWS Configuration (if using AWS provider)
AWS_AI_ENDPOINT=https://your-aws-endpoint
AWS_AI_API_KEY=your-aws-api-key

# Local AI Configuration (if using local provider)
LOCAL_AI_ENDPOINT=http://localhost:11434  # Default Ollama endpoint
```

#### 6. Initialize Database (Windows)
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Initialize database
python init_db.py
```

#### 7. Run Application (Windows)
```powershell
# Development mode
python main.py

# Production mode (install waitress for Windows)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 main:app
```

### 🐧 Linux/macOS Setup

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd school-management-system
```

#### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements-windows.txt
```

#### 3. Database Setup (Linux/macOS)
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres createdb school_management
sudo -u postgres createuser -P your_username

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE school_management TO your_username;"
```

#### 4. Environment Configuration
Create a `.env` file in the root directory (same as Windows section above)

#### 5. Initialize Database
```bash
python init_db.py
```

#### 6. Run Application
```bash
python main.py
# or
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 7. Access Application
Open your browser and navigate to `http://localhost:5000`

**Default Login Credentials:**
- **Admin**: admin@admin.com / admin123
- **Teacher**: teacher@teacher.com / teacher123
- **Student**: student@student.com / student123

## 🤖 AI Configuration Guide

### OpenAI Setup
1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Generate an API key
3. Set `AI_PROVIDER=openai` and `OPENAI_API_KEY=your-key` in environment

### AWS-Hosted Models
1. Configure your AWS AI endpoint
2. Set `AI_PROVIDER=aws`, `AWS_AI_ENDPOINT`, and `AWS_AI_API_KEY`
3. Ensure your endpoint supports OpenAI-compatible API format

### Local Models (Ollama)

#### Windows Installation
1. **Download and Install Ollama**:
   - Visit [ollama.ai/download](https://ollama.ai/download)
   - Download the Windows installer
   - Run the installer as Administrator
   - Ollama will be added to your system PATH

2. **Start Ollama Service** (Windows):
   ```powershell
   # Open PowerShell as Administrator
   ollama serve
   
   # Or start as a service (recommended)
   # Ollama should start automatically after installation
   ```

3. **Download Models** (Windows):
   ```powershell
   # Open a new PowerShell window
   # Download recommended models for different subjects
   ollama pull llama2:7b          # General purpose
   ollama pull codellama:7b       # Mathematics/Programming
   ollama pull mistral:7b         # Science/Technical
   ollama pull neural-chat:7b     # English/Literature
   ```

#### Linux/macOS Installation
1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama Service**:
   ```bash
   ollama serve
   ```

3. **Download Models**:
   ```bash
   # Download recommended models for different subjects
   ollama pull llama2:7b          # General purpose
   ollama pull codellama:7b       # Mathematics/Programming
   ollama pull mistral:7b         # Science/Technical
   ollama pull neural-chat:7b     # English/Literature
   ```

#### Configure Environment (All Platforms)
```env
AI_PROVIDER=local
LOCAL_AI_ENDPOINT=http://localhost:11434
```

5. **Model Selection by Subject**:
   Edit `ai_config.py` to specify which local model to use for each subject:
   ```python
   LOCAL_MODELS = {
       'mathematics': 'codellama:7b',
       'science': 'mistral:7b',
       'english': 'neural-chat:7b',
       'history': 'llama2:7b',
       'art': 'neural-chat:7b'
   }
   ```

### Demo Mode
If no AI provider is configured, the system automatically falls back to demo mode with predefined responses.

## 📊 Database Schema & Relationships

### Core Tables

#### Users Table
```sql
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'admin', 'teacher', 'student'
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    photo_url VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    -- Student-specific fields
    age INTEGER,
    learning_style VARCHAR(50),  -- 'visual', 'auditory', 'kinesthetic', 'reading'
    interests TEXT,  -- JSON string
    academic_goals TEXT,
    preferred_difficulty VARCHAR(20)  -- 'beginner', 'intermediate', 'advanced'
);
```

#### Classes Table
```sql
CREATE TABLE class (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    subject VARCHAR(50),  -- 'math', 'science', 'english', etc.
    teacher_id INTEGER NOT NULL REFERENCES user(id),
    ai_model_id INTEGER REFERENCES ai_model(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Assignments Table
```sql
CREATE TABLE assignment (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    class_id INTEGER NOT NULL REFERENCES class(id),
    due_date TIMESTAMP,
    max_points INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Assignment Submissions Table
```sql
CREATE TABLE assignment_submission (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id),
    student_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT,
    file_path VARCHAR(200),
    file_name VARCHAR(200),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Grades Table
```sql
CREATE TABLE grade (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id),
    student_id INTEGER NOT NULL REFERENCES user(id),
    submission_id INTEGER REFERENCES assignment_submission(id),
    grade FLOAT,
    feedback TEXT,
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graded_by INTEGER NOT NULL REFERENCES user(id)
);
```

### AI-Enhanced Tables

#### AI Models Table
```sql
CREATE TABLE ai_model (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,  -- 'math', 'science', 'english', etc.
    model_name VARCHAR(200) NOT NULL,  -- Model identifier
    fine_tuned_id VARCHAR(200),  -- Fine-tuned model ID
    prompt_template TEXT,  -- System prompt template
    max_tokens INTEGER DEFAULT 1000,
    temperature FLOAT DEFAULT 0.7,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Chat Messages Table
```sql
CREATE TABLE chat_message (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    class_id INTEGER NOT NULL REFERENCES class(id),
    ai_model_id INTEGER NOT NULL REFERENCES ai_model(id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL,  -- 'student', 'teacher', 'system'
    context_data TEXT,  -- JSON string of additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Student Profiles Table
```sql
CREATE TABLE student_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    learning_preferences TEXT,  -- JSON string
    study_patterns TEXT,  -- JSON string
    performance_metrics TEXT,  -- JSON string
    ai_interaction_history TEXT,  -- JSON string
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Relationship Mapping

```
┌─────────────┐
│    Users    │◄─┐
│ (id, email, │  │
│  role, ...)  │  │
└─────────────┘  │
        │        │
        │        │
        ▼        │
┌─────────────┐  │    ┌──────────────┐
│   Classes   │  │    │   Grades     │
│ (id, name,  │  │    │ (grade,      │
│ teacher_id) │  │    │  feedback)   │
└─────────────┘  │    └──────────────┘
        │        │           ▲
        │        │           │
        ▼        │           │
┌─────────────┐  │    ┌──────────────┐
│ Assignments │  │    │ Assignment   │
│ (title,     │  │    │ Submissions  │
│  due_date)  │  │    │ (content)    │
└─────────────┘  │    └──────────────┘
                 │
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
┌─────────────┐    ┌──────────────┐
│ Chat        │    │ Student      │
│ Messages    │    │ Profiles     │
│ (message,   │    │ (learning    │
│  response)  │    │  preferences)│
└─────────────┘    └──────────────┘
         │
         ▼
┌─────────────┐
│ AI Models   │
│ (subject,   │
│  model_name)│
└─────────────┘
```

### Key Relationships

1. **Users → Classes**: Many-to-many (students can enroll in multiple classes)
2. **Teachers → Classes**: One-to-many (teachers can teach multiple classes)
3. **Classes → Assignments**: One-to-many (classes have multiple assignments)
4. **Students → Submissions**: One-to-many (students submit multiple assignments)
5. **Submissions → Grades**: One-to-one (each submission gets one grade)
6. **Users → Chat Messages**: One-to-many (users have multiple AI conversations)
7. **Classes → AI Models**: Many-to-one (classes use subject-specific AI models)
8. **Users → Student Profiles**: One-to-one (students have extended profiles)

## 🗂️ Project Structure

```
school-management-system/
├── 📁 instance/                    # Database files (SQLite mode)
├── 📁 src/                        # React components (deprecated)
├── 📁 static/                     # Static CSS files
├── 📁 templates/                  # Jinja2 HTML templates
│   ├── admin_dashboard.html       # Enhanced admin interface
│   ├── student_dashboard.html     # AI tutor integration
│   ├── teacher_dashboard.html     # Teacher tools
│   ├── login.html                # Authentication
│   └── base.html                 # Base template
├── 📄 ai_config.py               # AI provider configuration
├── 📄 ai_service.py              # AI integration service
├── 📄 api_routes.py              # RESTful API endpoints
├── 📄 app.py                     # Flask application factory
├── 📄 auth.py                    # Authentication utilities
├── 📄 init_db.py                 # Database initialization
├── 📄 main.py                    # Application entry point
├── 📄 models.py                  # SQLAlchemy database models
├── 📄 routes.py                  # Web route handlers
├── 📄 requirements.txt           # Python dependencies
└── 📄 README.md                  # This documentation
```

## 🔧 Configuration Options

### AI Provider Configuration

#### OpenAI Configuration
```python
# ai_config.py
OPENAI_CONFIG = {
    'api_key': os.environ.get('OPENAI_API_KEY'),
    'model': 'gpt-4o',  # Latest model
    'temperature': 0.7,
    'max_tokens': 1000
}
```

#### Local Model Configuration
```python
# ai_config.py
LOCAL_CONFIG = {
    'endpoint': os.environ.get('LOCAL_AI_ENDPOINT', 'http://localhost:11434'),
    'models': {
        'mathematics': 'codellama:7b',
        'science': 'mistral:7b',
        'english': 'neural-chat:7b',
        'history': 'llama2:7b',
        'art': 'neural-chat:7b'
    }
}
```

### Database Configuration

#### Development (SQLite)
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
```

#### Production (PostgreSQL)
```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'pool_size': 10,
    'max_overflow': 20
}
```

## 🎯 Usage Guide

### Admin Functions

1. **User Management**:
   - Navigate to Admin Dashboard
   - Click "Manage Users" to view all users
   - Add new users with "Add New User"
   - Edit existing users by clicking on their entries

2. **Data Export**:
   - Click "Export Data" on Admin Dashboard
   - Select tables and specific columns
   - View relationship diagram
   - Download as ZIP file with CSV files

3. **AI Analytics**:
   - Click "AI Analytics" to view engagement metrics
   - Monitor student AI usage patterns
   - Review AI performance statistics

### Teacher Functions

1. **Class Management**:
   - View assigned classes on Teacher Dashboard
   - Create and manage assignments
   - Upload course materials
   - Access gradebook for grading

2. **Student Monitoring**:
   - View student profiles and performance
   - Monitor AI tutor interactions
   - Provide personalized feedback

### Student Functions

1. **Course Access**:
   - View enrolled classes
   - Access assignments and materials
   - Submit work through the platform

2. **AI Tutoring**:
   - Click "AI Tutor" on Student Dashboard
   - Select subject (Math, Science, English, History)
   - Engage in personalized conversations
   - Get homework help and concept explanations

## 🛠️ Development

### Setting Up Development Environment

#### Windows Development Setup
1. **Clone Repository**:
   ```powershell
   git clone <repository-url>
   cd school-management-system
   ```

2. **Create Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements-windows.txt
   ```

4. **Set Environment Variables** (Windows):
   ```powershell
   # Using PowerShell
   $env:FLASK_ENV="development"
   $env:FLASK_DEBUG="True"
   $env:DATABASE_URL="sqlite:///school_management.db"
   $env:SESSION_SECRET="dev-secret-key"
   
   # Or create a .env file (recommended)
   ```

5. **Initialize Database**:
   ```powershell
   python init_db.py
   ```

6. **Run Development Server**:
   ```powershell
   python main.py
   ```

#### Linux/macOS Development Setup
1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd school-management-system
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements-windows.txt
   ```

4. **Set Environment Variables**:
   ```bash
   export FLASK_ENV=development
   export FLASK_DEBUG=True
   export DATABASE_URL=sqlite:///school_management.db
   export SESSION_SECRET=dev-secret-key
   ```

5. **Initialize Database**:
   ```bash
   python init_db.py
   ```

6. **Run Development Server**:
   ```bash
   python main.py
   ```

### Adding New Features

#### Adding a New AI Model
1. Update `ai_config.py` with model configuration
2. Add model entry to `init_db.py`
3. Update `ai_service.py` to handle the new model
4. Modify templates to include the new subject option

#### Adding New Database Tables
1. Define model in `models.py`
2. Create migration script
3. Update `init_db.py` with sample data
4. Add API endpoints in `api_routes.py`
5. Update export functionality in admin dashboard

#### Customizing AI Responses
1. Modify prompt templates in `ai_service.py`
2. Add context data collection methods
3. Update student profile integration
4. Test with different AI providers

### Testing

#### Unit Testing
```bash
python -m pytest tests/
```

#### Integration Testing
```bash
python -m pytest tests/integration/
```

#### Manual Testing
1. Test all user roles (admin, teacher, student)
2. Verify AI functionality with different providers
3. Test data export with various selections
4. Validate authentication and authorization

## 🚀 Deployment

### Production Deployment

#### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

#### Environment Variables for Production
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/dbname
SESSION_SECRET=your-super-secure-secret-key
AI_PROVIDER=openai
OPENAI_API_KEY=your-production-openai-key
```

#### Database Migration
```bash
# Backup existing database
pg_dump school_management > backup.sql

# Run migrations
flask db upgrade

# Verify integrity
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Performance Optimization

1. **Database Optimization**:
   - Add indexes on frequently queried columns
   - Use connection pooling
   - Implement query optimization

2. **Caching**:
   - Implement Redis for session storage
   - Cache AI responses for common questions
   - Use CDN for static assets

3. **AI Performance**:
   - Implement response caching
   - Use async AI calls where possible
   - Load balance across multiple AI providers

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Issues

**Windows:**
```powershell
# Check PostgreSQL service status
Get-Service postgresql*

# Start PostgreSQL service
Start-Service postgresql-x64-17

# Check connection
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U username -d school_management
```

**Linux/macOS:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check connection
psql -h localhost -U username -d school_management
```

#### AI Provider Issues
1. **OpenAI API Errors**:
   - Verify API key validity
   - Check rate limits and quotas
   - Ensure proper internet connectivity

2. **Local Model Issues**:
   
   **Windows:**
   ```powershell
   # Verify Ollama is running
   ollama list
   
   # Check model availability
   ollama pull model-name
   
   # Verify endpoint accessibility
   Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
   ```
   
   **Linux/macOS:**
   ```bash
   # Verify Ollama is running
   ollama list
   
   # Check model availability
   ollama pull model-name
   
   # Verify endpoint accessibility
   curl http://localhost:11434/api/tags
   ```

3. **AWS Model Issues**:
   - Verify endpoint URL and API key
   - Check AWS service status
   - Validate API compatibility

#### Performance Issues
1. **Slow Database Queries**:
   - Add indexes to frequently queried columns
   - Optimize complex joins
   - Use database query profiling

2. **Memory Usage**:
   - Monitor AI model memory consumption
   - Implement proper connection pooling
   - Use memory profiling tools

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable Flask debug mode
app.debug = True
```

## 📈 Monitoring and Analytics

### Application Metrics
- User activity tracking
- AI interaction frequency
- Database query performance
- Error rate monitoring

### AI Analytics
- Response quality assessment
- Student engagement metrics
- Learning outcome correlation
- Model performance comparison

### System Health
- Database connection monitoring
- AI provider availability
- Response time tracking
- Resource utilization metrics

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request
5. Code review and merge

### Code Standards
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write comprehensive docstrings
- Maintain test coverage above 80%

### Documentation
- Update README for new features
- Document API changes
- Include configuration examples
- Provide troubleshooting guides

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- OpenAI for advanced AI capabilities
- Ollama for local AI model support
- Bootstrap team for the responsive UI framework
- PostgreSQL for robust database management

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with detailed information
4. Contact the development team

---

**Version 2.0.0** - AI-Enhanced School Management System
*Built with ❤️ for modern education*