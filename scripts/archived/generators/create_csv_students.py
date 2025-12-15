#!/usr/bin/env python3
"""
Create new students from CSV data to test enhanced AI personalization
"""

import os
import csv
import json
from datetime import datetime, date
from app import app, db
from models import User, Class
from auth import hash_password

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
            return eval(activities_str)
        else:
            return [activities_str.strip()]
    except:
        return []

def parse_attendance(attendance_str):
    """Parse attendance percentage"""
    if not attendance_str or attendance_str.strip() == '':
        return None
    try:
        return float(attendance_str.replace('%', '').strip())
    except ValueError:
        return None

def assign_learning_style(activities):
    """Assign learning style based on activities"""
    activities_lower = [act.lower() for act in activities]
    
    if any(term in ' '.join(activities_lower) for term in ['art', 'drama', 'chess']):
        return 'visual'
    elif any(term in ' '.join(activities_lower) for term in ['music', 'debating', 'cultural']):
        return 'auditory'
    elif any(term in ' '.join(activities_lower) for term in ['rugby', 'football', 'basketball', 'cricket', 'volleyball']):
        return 'kinesthetic'
    else:
        return 'reading'

def main():
    """Create students from CSV data"""
    csv_file = 'attached_assets/Example - NZ_Student_Management_System_Data_1752275839402.csv'
    
    with app.app_context():
        # Read CSV and create unique students
        students_created = 0
        seen_students = set()
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Use NSN as unique identifier, only take Year 11 students
                nsn = row['NSN'].strip()
                year_level = row['Year Level'].strip()
                
                if year_level != 'Year 11' or nsn in seen_students:
                    continue
                
                seen_students.add(nsn)
                
                first_name = row['First Name'].strip()
                last_name = row['Last Name'].strip()
                
                # Check if student already exists
                existing = User.query.filter_by(
                    first_name=first_name,
                    last_name=last_name,
                    role='student'
                ).first()
                
                if existing:
                    print(f"Student {first_name} {last_name} already exists, skipping")
                    continue
                
                # Create email from name
                email = f"{first_name.lower()}.{last_name.lower()}@student.school.nz"
                
                # Parse data
                activities = parse_activities(row.get('Extra-curricular Activities', ''))
                date_of_birth = parse_date(row.get('Date of Birth', ''))
                
                # Calculate average attendance
                attendance_values = []
                for term in ['Attendance_Term 1', 'Attendance_Term 2', 'Attendance_Term 3', 'Attendance_Term 4']:
                    att = parse_attendance(row.get(term, ''))
                    if att is not None:
                        attendance_values.append(att)
                avg_attendance = sum(attendance_values) / len(attendance_values) if attendance_values else None
                
                # Calculate age
                age = None
                if date_of_birth:
                    today = date.today()
                    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                
                # Create new student
                student = User(
                    email=email,
                    password_hash=hash_password('student123'),  # Default password
                    role='student',
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    gender=row.get('Gender', '').strip() or None,
                    ethnicity=row.get('Ethnicity', '').strip() or None,
                    date_of_birth=date_of_birth,
                    year_level=year_level,
                    primary_language=row.get('Primary Language', '').strip() or None,
                    secondary_language=row.get('Secondary Language', '').strip() or None,
                    learning_difficulty=row.get('Learning Difficulty', '').strip() or None,
                    major_life_event=row.get('Major Life Event', '').strip() or None,
                    attendance_rate=avg_attendance,
                    learning_style=assign_learning_style(activities),
                    academic_goals=f"Excel in {year_level} studies and prepare for university",
                    preferred_difficulty='intermediate'
                )
                
                # Set activities and interests
                student.set_extracurricular_list(activities)
                interests = ['Learning', 'Academic achievement'] + activities[:2]
                student.set_interests_list(interests)
                
                db.session.add(student)
                students_created += 1
                
                print(f"Created student: {first_name} {last_name} ({email})")
                
                # Stop after creating 5 students for testing
                if students_created >= 5:
                    break
        
        # Enroll new students in existing classes
        math_class = Class.query.filter_by(subject='mathematics').first()
        science_class = Class.query.filter_by(subject='science').first()
        
        if math_class and science_class:
            new_students = User.query.filter_by(role='student').order_by(User.id.desc()).limit(students_created).all()
            
            for student in new_students:
                if student not in math_class.users:
                    math_class.users.append(student)
                if student not in science_class.users:
                    science_class.users.append(student)
        
        db.session.commit()
        print(f"\nSuccessfully created {students_created} students with enhanced AI profiles!")
        print("Each student has:")
        print("- Complete demographic information")
        print("- Learning style and preferences")
        print("- Academic goals and interests")
        print("- Learning difficulties (if applicable)")
        print("- Cultural and language background")
        print("- Attendance and performance data")

if __name__ == "__main__":
    main()