import sqlite3
import json
from datetime import datetime

def create_database():
    """Create the school_ai.db database with student_profiles table"""
    conn = sqlite3.connect('school_ai.db')
    cursor = conn.cursor()
    
    # Create student_profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            last_interaction TEXT,
            chat_history TEXT DEFAULT '[]',
            understanding_score REAL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database 'school_ai.db' created successfully with 'student_profiles' table.")

if __name__ == "__main__":
    create_database()
