#!/usr/bin/env python3
"""
Database migration script to add enhanced student profile fields
"""

from app import app, db

def migrate_student_profiles():
    """Add new student profile columns to the database"""
    
    with app.app_context():
        try:
            # List of new columns to add
            new_columns = [
                ("gender", "VARCHAR(20)"),
                ("ethnicity", "VARCHAR(100)"),
                ("date_of_birth", "DATE"),
                ("year_level", "VARCHAR(20)"),
                ("primary_language", "VARCHAR(50)"),
                ("secondary_language", "VARCHAR(50)"),
                ("learning_difficulty", "VARCHAR(100)"),
                ("extracurricular_activities", "TEXT"),
                ("major_life_event", "VARCHAR(200)"),
                ("attendance_rate", "FLOAT")
            ]
            
            print("Starting database migration for enhanced student profiles...")
            
            # Check which columns already exist
            existing_columns = []
            for column_name, column_type in new_columns:
                try:
                    # Try to query a column to see if it exists
                    db.session.execute(f"SELECT {column_name} FROM \"user\" LIMIT 1")
                    existing_columns.append(column_name)
                    print(f"Column '{column_name}' already exists")
                except Exception:
                    # Column doesn't exist, we need to add it
                    print(f"Adding column '{column_name}' of type {column_type}")
                    try:
                        db.session.execute(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_type}')
                        db.session.commit()
                        print(f"✓ Successfully added column '{column_name}'")
                    except Exception as e:
                        print(f"✗ Error adding column '{column_name}': {e}")
                        db.session.rollback()
                        
            print("\nDatabase migration completed!")
            print(f"Enhanced student profiles are now ready for AI personalization")
            
            # Now run the data population
            print("\nStarting student data population...")
            import populate_student_data
            populate_student_data.main()
            
        except Exception as e:
            print(f"Migration error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_student_profiles()