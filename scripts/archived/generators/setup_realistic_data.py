#!/usr/bin/env python3
"""
Setup realistic school data with limited classes, teachers, and students
"""
from app import app, db
from models import User, Class, Assignment, AssignmentSubmission, Grade
from auth import hash_password
from datetime import datetime, timedelta
import random

def setup_realistic_data():
    """Create realistic but limited dataset"""
    with app.app_context():
        # Clear existing data in proper order to avoid foreign key constraints
        print("Clearing existing data...")
        from models import ContentFile, ChatMessage
        Grade.query.delete()
        AssignmentSubmission.query.delete()
        Assignment.query.delete()
        ContentFile.query.delete()
        ChatMessage.query.delete()
        # Clear class enrollments (many-to-many relationship)
        db.session.execute(db.text("DELETE FROM class_users"))
        Class.query.delete()
        
        # Keep only essential users and remove extras
        User.query.filter(~User.email.in_([
            'admin@admin.com',
            'teacher@teacher.com', 
            'student@student.com'
        ])).delete()
        
        # Create 3 additional teachers (total 4 including teacher@teacher.com)
        teachers_data = [
            {'email': 'math.teacher@school.com', 'first_name': 'Sarah', 'last_name': 'Johnson'},
            {'email': 'science.teacher@school.com', 'first_name': 'Michael', 'last_name': 'Chen'},
            {'email': 'english.teacher@school.com', 'first_name': 'Emma', 'last_name': 'Davis'},
        ]
        
        for teacher_data in teachers_data:
            if not User.query.filter_by(email=teacher_data['email']).first():
                teacher = User(
                    email=teacher_data['email'],
                    password_hash=hash_password('teacher123'),
                    first_name=teacher_data['first_name'],
                    last_name=teacher_data['last_name'],
                    role='teacher',
                    is_active=True
                )
                db.session.add(teacher)
        
        # Create 3 additional students (total 4 including student@student.com)
        students_data = [
            {'email': 'alice.student@school.com', 'first_name': 'Alice', 'last_name': 'Smith'},
            {'email': 'bob.student@school.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
            {'email': 'carol.student@school.com', 'first_name': 'Carol', 'last_name': 'Brown'},
        ]
        
        for student_data in students_data:
            if not User.query.filter_by(email=student_data['email']).first():
                student = User(
                    email=student_data['email'],
                    password_hash=hash_password('student123'),
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    role='student',
                    is_active=True,
                    learning_style='visual',
                    preferred_difficulty='intermediate',
                    academic_goals='Improve grades and understanding'
                )
                db.session.add(student)
        
        db.session.commit()
        
        # Get all teachers and students
        teachers = User.query.filter_by(role='teacher', is_active=True).all()
        students = User.query.filter_by(role='student', is_active=True).all()
        
        print(f"Found {len(teachers)} teachers and {len(students)} students")
        
        # Create 4 classes with realistic subjects
        classes_data = [
            {'name': 'Mathematics 101', 'subject': 'Mathematics', 'description': 'Introduction to Algebra and Geometry'},
            {'name': 'Biology Fundamentals', 'subject': 'Science', 'description': 'Basic principles of life sciences'},
            {'name': 'English Literature', 'subject': 'English', 'description': 'Classic and modern literature analysis'},
            {'name': 'World History', 'subject': 'History', 'description': 'Global historical perspectives'},
        ]
        
        for i, class_data in enumerate(classes_data):
            teacher = teachers[i % len(teachers)]  # Distribute classes among teachers
            
            new_class = Class(
                name=class_data['name'],
                subject=class_data['subject'],
                description=class_data['description'],
                teacher_id=teacher.id,
                is_active=True
            )
            db.session.add(new_class)
            db.session.flush()  # Get the ID
            
            # Enroll all students in each class (realistic for small school)
            for student in students:
                # Use the many-to-many relationship table
                db.session.execute(db.text(
                    "INSERT INTO class_users (class_id, user_id) VALUES (:class_id, :user_id)"
                ), {"class_id": new_class.id, "user_id": student.id})
            
            print(f"Created class: {class_data['name']} with teacher {teacher.get_full_name()}")
        
        db.session.commit()
        
        # Create realistic assignments for each class
        classes = Class.query.all()
        for class_obj in classes:
            assignments_data = [
                {'title': f'{class_obj.subject} Assignment 1', 'description': 'First assignment covering basic concepts', 'max_points': 100},
                {'title': f'{class_obj.subject} Midterm Project', 'description': 'Comprehensive project demonstrating understanding', 'max_points': 150},
                {'title': f'{class_obj.subject} Quiz Series', 'description': 'Weekly quiz assessments', 'max_points': 75},
            ]
            
            for assign_data in assignments_data:
                assignment = Assignment(
                    title=assign_data['title'],
                    description=assign_data['description'],
                    class_id=class_obj.id,
                    due_date=datetime.now() + timedelta(days=random.randint(7, 30)),
                    max_points=assign_data['max_points'],
                    is_active=True
                )
                db.session.add(assignment)
                db.session.flush()
                
                # Create submissions and grades for some students
                for student in class_obj.students[:3]:  # First 3 students submit
                    submission = AssignmentSubmission(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        content=f"Sample submission content for {assignment.title}",
                        submitted_at=datetime.now() - timedelta(days=random.randint(1, 5))
                    )
                    db.session.add(submission)
                    db.session.flush()
                    
                    # Add grades
                    grade_value = random.randint(75, 95)  # Realistic grade range
                    grade = Grade(
                        assignment_id=assignment.id,
                        student_id=student.id,
                        submission_id=submission.id,
                        grade=grade_value,
                        feedback=f"Good work! Score: {grade_value}/{assignment.max_points}",
                        graded_at=datetime.now(),
                        graded_by=class_obj.teacher_id
                    )
                    db.session.add(grade)
        
        db.session.commit()
        print("Realistic data setup completed successfully!")
        
        # Print summary
        total_classes = Class.query.count()
        total_assignments = Assignment.query.count()
        total_submissions = AssignmentSubmission.query.count()
        total_grades = Grade.query.count()
        
        print(f"\nData Summary:")
        print(f"- Classes: {total_classes}")
        print(f"- Teachers: {len(teachers)}")
        print(f"- Students: {len(students)}")
        print(f"- Assignments: {total_assignments}")
        print(f"- Submissions: {total_submissions}")
        print(f"- Grades: {total_grades}")

if __name__ == '__main__':
    setup_realistic_data()