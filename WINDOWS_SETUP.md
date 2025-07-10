# 🖥️ Windows Setup Guide

Complete setup guide for running the AI-Enhanced School Management System on Windows.

## Prerequisites

- Windows 10 or 11
- Git for Windows
- Python 3.11 or higher
- Administrator access for PostgreSQL installation

## Step-by-Step Installation

### 1. Install Git for Windows

1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default settings
3. Choose "Git from the command line and also from 3rd-party software"
4. Choose "Checkout Windows-style, commit Unix-style line endings"

### 2. Install Python

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/windows/)
2. **Important**: Check "Add Python to PATH" during installation
3. Choose "Install for all users" if you have admin rights
4. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### 3. Install PostgreSQL

1. Download PostgreSQL 16 from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer as Administrator
3. During installation:
   - Set a password for the 'postgres' user (remember this!)
   - Port: 5432 (default)
   - Locale: Default locale
   - Install pgAdmin 4 (recommended)
   - Install Stack Builder (optional)

### 4. Clone the Project

```powershell
# Open PowerShell
cd C:\
mkdir Projects
cd Projects
git clone <repository-url>
cd school-management-system
```

### 5. Setup Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements-windows.txt
```

### 6. Setup Database

#### Method 1: Using Command Line
```powershell
# Navigate to PostgreSQL bin directory
cd "C:\Program Files\PostgreSQL\16\bin"

# Create database
.\createdb.exe -U postgres school_management

# Create user (you'll be prompted for passwords)
.\createuser.exe -U postgres -P schooluser

# Connect to PostgreSQL
.\psql.exe -U postgres -d school_management
```

In the PostgreSQL shell:
```sql
-- Grant privileges to the new user
GRANT ALL PRIVILEGES ON DATABASE school_management TO schooluser;
\q
```

#### Method 2: Using pgAdmin 4 (GUI)
1. Open pgAdmin 4 from Start Menu
2. Connect using the postgres password you set during installation
3. Right-click "Databases" → "Create" → "Database"
4. Name: `school_management`
5. Right-click "Login/Group Roles" → "Create" → "Login/Group Role"
6. Name: `schooluser`, set password, grant privileges

### 7. Configure Environment

Create a `.env` file in the project root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://schooluser:your_password@localhost:5432/school_management
PGHOST=localhost
PGPORT=5432
PGUSER=schooluser
PGPASSWORD=your_password
PGDATABASE=school_management

# Security
SESSION_SECRET=your-super-secret-key-here-change-this

# AI Provider Configuration
AI_PROVIDER=demo  # Start with demo mode

# Optional: OpenAI Configuration
# OPENAI_API_KEY=sk-your-openai-api-key

# Optional: Local AI Configuration
# AI_PROVIDER=local
# LOCAL_AI_ENDPOINT=http://localhost:11434
```

### 8. Initialize Database

```powershell
# Make sure virtual environment is active
.\venv\Scripts\Activate.ps1

# Initialize database with sample data
python init_db.py
```

You should see output like:
```
Dummy users initialized successfully.
AI models initialized successfully.
Dummy classes and assignments initialized successfully.
Sample chat history initialized successfully.
Student profiles initialized successfully.
```

### 9. Run the Application

```powershell
# Development mode
python main.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 10. Access the Application

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. Use these default login credentials:
   - **Admin**: admin@admin.com / admin123
   - **Teacher**: teacher@teacher.com / teacher123
   - **Student**: student@student.com / student123

## Optional: AI Setup

### OpenAI Setup
1. Get an API key from [OpenAI Platform](https://platform.openai.com/)
2. Update your `.env` file:
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

### Local AI Setup (Ollama)
1. Download Ollama from [ollama.ai](https://ollama.ai/download)
2. Install and run the application
3. Download models:
   ```powershell
   ollama pull llama2:7b
   ollama pull codellama:7b
   ```
4. Update your `.env` file:
   ```env
   AI_PROVIDER=local
   LOCAL_AI_ENDPOINT=http://localhost:11434
   ```

## Common Windows Issues

### PowerShell Execution Policy Error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### PostgreSQL Service Not Running
```powershell
# Check service status
Get-Service postgresql*

# Start service
Start-Service postgresql-x64-16
```

### Python Not Found
- Reinstall Python with "Add to PATH" checked
- Or manually add Python to PATH:
  1. Search "Environment Variables" in Start Menu
  2. Edit "Path" variable
  3. Add Python installation directory

### Port 5000 Already in Use
```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or run on different port
python main.py --port 5001
```

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check firewall settings
3. Verify credentials in `.env` file
4. Test connection:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U schooluser -d school_management
   ```

## Production Deployment on Windows

### Using Waitress (Recommended for Windows)
```powershell
# Install waitress
pip install waitress

# Run production server
waitress-serve --host=0.0.0.0 --port=5000 main:app
```

### As Windows Service
Consider using `nssm` (Non-Sucking Service Manager) to run as a Windows service:

1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Install as service:
   ```cmd
   nssm install SchoolManagementSystem
   ```
3. Configure path to your Python executable and script
4. Start service:
   ```cmd
   nssm start SchoolManagementSystem
   ```

## File Permissions

Ensure the application has write permissions to:
- Database file location (if using SQLite)
- Upload directories
- Log directories

```powershell
# Give full control to current user
icacls "C:\Projects\school-management-system" /grant:r "%USERNAME%":(OI)(CI)F
```

## Firewall Configuration

If accessing from other machines on the network:

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Create new Inbound Rule
4. Port: 5000
5. Protocol: TCP
6. Action: Allow

## Backup and Maintenance

### Database Backup
```powershell
# Navigate to PostgreSQL bin directory
cd "C:\Program Files\PostgreSQL\16\bin"

# Create backup
.\pg_dump.exe -h localhost -U schooluser -d school_management > backup_$(Get-Date -Format 'yyyyMMdd').sql
```

### Automated Backup Script
Create `backup.ps1`:
```powershell
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "C:\Backups\school_management_$date.sql"

& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -h localhost -U schooluser -d school_management > $backupPath

Write-Host "Backup created: $backupPath"
```

Run via Task Scheduler for automated backups.

## Performance Tips

1. **SSD Storage**: Install on SSD for better database performance
2. **RAM**: Minimum 8GB recommended, 16GB+ for production
3. **Antivirus**: Add project folder to antivirus exclusions
4. **Windows Updates**: Keep system updated for security

## Support

If you encounter issues:

1. Check Windows Event Viewer for system errors
2. Review application logs
3. Verify all services are running
4. Test database connectivity separately
5. Check Windows Firewall settings

Remember to update your `.env` file with actual values and never commit sensitive information to version control!