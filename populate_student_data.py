#!/usr/bin/env python3
"""
Script to populate existing students with comprehensive profile data from CSV
This script enhances the AI personalization capabilities by adding detailed student profiles
"""

import os
import sys
import csv
import json
from datetime import datetime, date
from app import app, db
from models import User

def parse_date(date_str):
    """Parse date from DD/MM/YYYY format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        return None

def parse_activities(activities_str):
    """Parse extracurricular activities from string"""
    if not activities_str or activities_str.strip() == '':
        return []
    try:
        # Handle both string and list formats
        if activities_str.startswith('[') and activities_str.endswith(']'):
            return eval(activities_str)  # Safely parse list string
        else:
            return [activities_str.strip()]
    except:
        return []

def parse_attendance(attendance_str):
    """Parse attendance percentage"""
    if not attendance_str or attendance_str.strip() == '':
        return None
    try:
        # Remove % sign and convert to float
        return float(attendance_str.replace('%', '').strip())
    except ValueError:
        return None

def assign_learning_style(activities, interests):
    """Assign learning style based on activities and interests"""
    activities_lower = [act.lower() for act in activities]
    
    # Visual learners
    if any(term in ' '.join(activities_lower) for term in ['art', 'drama', 'chess']):
        return 'visual'
    
    # Auditory learners  
    if any(term in ' '.join(activities_lower) for term in ['music', 'debating', 'cultural']):
        return 'auditory'
    
    # Kinesthetic learners
    if any(term in ' '.join(activities_lower) for term in ['rugby', 'football', 'basketball', 'cricket', 'volleyball']):
        return 'kinesthetic'
    
    # Reading/writing learners
    if any(term in ' '.join(activities_lower) for term in ['coding', 'environment']):
        return 'reading'
    
    return 'visual'  # Default

def assign_academic_goals(year_level, ethnicity):
    """Assign academic goals based on year level and background"""
    goals = [
        "Improve grades and understanding",
        "Prepare for university entrance",
        "Develop critical thinking skills",
        "Build confidence in learning"
    ]
    
    if year_level == 'Year 13':
        goals.append("Prepare for NCEA Level 3 excellence")
        goals.append("University scholarship preparation")
    elif year_level == 'Year 12':
        goals.append("Achieve NCEA Level 2 with merit")
    else:
        goals.append("Build strong foundation skills")
        
    if ethnicity in ['Māori', 'Pasifika']:
        goals.append("Connect learning to cultural identity")
    
    return '; '.join(goals[:3])

def assign_interests(activities, subjects):
    """Generate interests based on activities and academic performance"""
    interests = []
    
    # Map activities to interests
    activity_interests = {
        'cricket': 'Sports and teamwork',
        'rugby': 'Physical fitness and strategy', 
        'football': 'Team sports',
        'basketball': 'Athletics and coordination',
        'volleyball': 'Team dynamics',
        'art club': 'Creative arts and design',
        'drama club': 'Performance and creativity',
        'music club': 'Musical arts',
        'chess club': 'Strategy and logic',
        'coding club': 'Technology and programming',
        'debating': 'Public speaking and argumentation',
        'cultural group': 'Cultural heritage and identity',
        'environment club': 'Environmental science'
    }
    
    for activity in activities:
        activity_lower = activity.lower()
        for key, interest in activity_interests.items():
            if key in activity_lower:
                interests.append(interest)
    
    # Add academic interests
    interests.extend(['Learning and education', 'Problem solving'])
    
    return list(set(interests))  # Remove duplicates

def main():
    """Main function to populate student data"""
    csv_file = 'attached_assets/Example - NZ_Student_Management_System_Data_1752275839402.csv'
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        return
    
    print("Starting student data population...")
    
    with app.app_context():
        # Get existing students
        existing_students = User.query.filter_by(role='student').all()
        print(f"Found {len(existing_students)} existing students")
        
        # Read CSV data
        student_data = {}
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                first_name = row['First Name'].strip()
                last_name = row['Last Name'].strip()
                key = f"{first_name.lower()}_{last_name.lower()}"
                
                if key not in student_data:
                    student_data[key] = []
                student_data[key].append(row)
        
        print(f"Loaded data for {len(student_data)} unique students from CSV")
        
        updated_count = 0
        
        # Update existing students with CSV data
        for student in existing_students:
            student_key = f"{student.first_name.lower()}_{student.last_name.lower()}"
            
            if student_key in student_data:
                # Use the most recent year data (last entry)
                csv_student = student_data[student_key][-1]
                
                print(f"Updating student: {student.first_name} {student.last_name}")
                
                # Update basic profile fields
                student.gender = csv_student.get('Gender', '').strip() or None
                student.ethnicity = csv_student.get('Ethnicity', '').strip() or None
                student.date_of_birth = parse_date(csv_student.get('Date of Birth', ''))
                student.year_level = csv_student.get('Year Level', '').strip() or None
                student.primary_language = csv_student.get('Primary Language', '').strip() or None
                student.secondary_language = csv_student.get('Secondary Language', '').strip() or None
                student.learning_difficulty = csv_student.get('Learning Difficulty', '').strip() or None
                student.major_life_event = csv_student.get('Major Life Event', '').strip() or None
                
                # Parse and set extracurricular activities
                activities = parse_activities(csv_student.get('Extra-curricular Activities', ''))
                student.set_extracurricular_list(activities)
                
                # Calculate average attendance from all terms
                attendance_values = []
                for term in ['Attendance_Term 1', 'Attendance_Term 2', 'Attendance_Term 3', 'Attendance_Term 4']:
                    att = parse_attendance(csv_student.get(term, ''))
                    if att is not None:
                        attendance_values.append(att)
                
                if attendance_values:
                    student.attendance_rate = sum(attendance_values) / len(attendance_values)
                
                # Assign AI-related fields
                student.learning_style = assign_learning_style(activities, [])
                student.academic_goals = assign_academic_goals(student.year_level, student.ethnicity)
                student.set_interests_list(assign_interests(activities, []))
                
                # Set preferred difficulty based on performance (simplified)
                if student.attendance_rate and student.attendance_rate > 90:
                    student.preferred_difficulty = 'advanced'
                elif student.attendance_rate and student.attendance_rate > 80:
                    student.preferred_difficulty = 'intermediate'
                else:
                    student.preferred_difficulty = 'beginner'
                
                # Calculate age from date of birth
                if student.date_of_birth:
                    today = date.today()
                    student.age = today.year - student.date_of_birth.year - ((today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day))
                
                updated_count += 1
            else:
                print(f"No CSV data found for student: {student.first_name} {student.last_name}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} students with enhanced profile data!")
            print("Students now have comprehensive AI personalization data including:")
            print("- Biological profile (gender, ethnicity, age)")
            print("- Learning accommodations (difficulties, language)")
            print("- Learning style and preferences")
            print("- Academic goals and interests")
            print("- Attendance and performance metrics")
            
        except Exception as e:
            print(f"Error saving to database: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main()