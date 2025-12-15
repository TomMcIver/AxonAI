#!/usr/bin/env python3
"""
Database migration script to add quizzes table
"""

import sqlite3

def migrate_database():
    """Add quizzes table to the database"""
    conn = sqlite3.connect('school_ai.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Adding Quizzes Table to Database")
    print("=" * 60)
    
    # Check if table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='quizzes'
    """)
    
    if cursor.fetchone():
        print("\n⚠ Table 'quizzes' already exists, skipping...")
    else:
        print("\n✓ Creating 'quizzes' table...")
        cursor.execute('''
            CREATE TABLE quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT DEFAULT '[]',
                score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES student_profiles(id)
            )
        ''')
        print("  Table 'quizzes' created successfully!")
    
    conn.commit()
    
    # Verify the schema
    print("\n" + "=" * 60)
    print("Quizzes Table Schema:")
    print("=" * 60)
    cursor.execute("PRAGMA table_info(quizzes)")
    for column in cursor.fetchall():
        print(f"  {column[1]:20} {column[2]:10} {'NOT NULL' if column[3] else ''}")
    
    conn.close()
    print("\n✅ Migration completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    migrate_database()
