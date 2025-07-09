from app import db
from models import User, Class, Assignment, AssignmentSubmission, Grade
from auth import hash_password
from datetime import datetime, timedelta

def init_dummy_users():
    """Initialize dummy users for testing"""
    dummy_users = [
        {
            'email': 'admin@admin.com',
            'password': 'admin123',
            'role': 'admin',
            'first_name': 'Admin',
            'last_name': 'User'
        },
        {
            'email': 'teacher@teacher.com',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Teacher',
            'last_name': 'Smith'
        },
        {
            'email': 'student@student.com',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Student',
            'last_name': 'Johnson'
        }
    ]
    
    for user_data in dummy_users:
        # Check if user already exists
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(
                email=user_data['email'],
                password_hash=hash_password(user_data['password']),
                role=user_data['role'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            db.session.add(user)
    
    try:
        db.session.commit()
        print("Dummy users initialized successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing dummy users: {e}")

def init_dummy_classes():
    """Initialize dummy classes and assignments for testing"""
    try:
        # Get teacher and student
        teacher = User.query.filter_by(email='teacher@teacher.com').first()
        student = User.query.filter_by(email='student@student.com').first()
        
        if not teacher or not student:
            print("Teacher or student not found, skipping class initialization")
            return
        
        # Create dummy classes
        dummy_classes = [
            {
                'name': 'Mathematics 101',
                'description': 'Basic algebra and geometry',
                'teacher_id': teacher.id
            },
            {
                'name': 'English Literature',
                'description': 'Introduction to classic literature',
                'teacher_id': teacher.id
            },
            {
                'name': 'Science Basics',
                'description': 'Chemistry and physics fundamentals',
                'teacher_id': teacher.id
            }
        ]
        
        for class_data in dummy_classes:
            existing_class = Class.query.filter_by(name=class_data['name']).first()
            if not existing_class:
                new_class = Class(
                    name=class_data['name'],
                    description=class_data['description'],
                    teacher_id=class_data['teacher_id']
                )
                # Add student to class
                new_class.users.append(student)
                db.session.add(new_class)
        
        db.session.commit()
        
        # Create dummy assignments
        classes = Class.query.all()
        for class_obj in classes:
            assignment = Assignment(
                title=f"Assignment 1 - {class_obj.name}",
                description=f"Complete the exercises for {class_obj.name}",
                class_id=class_obj.id,
                due_date=datetime.now() + timedelta(days=7),
                max_points=100
            )
            db.session.add(assignment)
        
        db.session.commit()
        print("Dummy classes and assignments initialized successfully.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing dummy classes: {e}")
