from app import db
from models import User
from auth import hash_password

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
