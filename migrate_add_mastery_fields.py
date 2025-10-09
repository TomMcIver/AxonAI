#!/usr/bin/env python3
"""
Database migration script to add mastery tracking fields
"""

import sqlite3

def migrate_database():
    """Add mastery_levels and trend columns to student_profiles table"""
    conn = sqlite3.connect('school_ai.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Adding Mastery Tracking Fields to Database")
    print("=" * 60)
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(student_profiles)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add mastery_levels column if it doesn't exist
    if 'mastery_levels' not in columns:
        print("\n✓ Adding 'mastery_levels' column (JSON)...")
        cursor.execute('''
            ALTER TABLE student_profiles 
            ADD COLUMN mastery_levels TEXT DEFAULT '{}'
        ''')
        print("  Column 'mastery_levels' added successfully!")
    else:
        print("\n⚠ Column 'mastery_levels' already exists, skipping...")
    
    # Add trend column if it doesn't exist
    if 'trend' not in columns:
        print("\n✓ Adding 'trend' column (TEXT)...")
        cursor.execute('''
            ALTER TABLE student_profiles 
            ADD COLUMN trend TEXT DEFAULT 'flat'
        ''')
        print("  Column 'trend' added successfully!")
    else:
        print("\n⚠ Column 'trend' already exists, skipping...")
    
    conn.commit()
    
    # Verify the updated schema
    print("\n" + "=" * 60)
    print("Updated Schema:")
    print("=" * 60)
    cursor.execute("PRAGMA table_info(student_profiles)")
    for column in cursor.fetchall():
        print(f"  {column[1]:20} {column[2]:10} {'NOT NULL' if column[3] else ''}")
    
    conn.close()
    print("\n✅ Migration completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    migrate_database()
