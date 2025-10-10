"""
Create 3 simulated students with different learning profiles
These are regular students in the database - nothing special or hardcoded
"""
from app import app, db
from models import User, Class
import sys

def create_simulated_students():
    """Create 3 student accounts with different learning characteristics"""
    with app.app_context():
        # Check if simulated students already exist
        existing_alex = User.query.filter_by(first_name='Alex', last_name='Simulated').first()
        if existing_alex:
            print("Simulated students already exist!")
            alex = existing_alex
            jordan = User.query.filter_by(first_name='Jordan', last_name='Simulated').first()
            taylor = User.query.filter_by(first_name='Taylor', last_name='Simulated').first()
            print(f"Alex ID: {alex.id}, Jordan ID: {jordan.id}, Taylor ID: {taylor.id}")
            return alex.id, jordan.id, taylor.id
        
        # Get a test class to enroll them in
        test_class = Class.query.filter_by(is_active=True).first()
        if not test_class:
            print("Error: No active classes found. Please create a class first.")
            sys.exit(1)
        
        print(f"Will enroll students in: {test_class.name} (ID: {test_class.id})")
        
        # Create Alex - High Performer
        alex = User(
            role='student',
            first_name='Alex',
            last_name='Simulated',
            year_level='Year 12',
            learning_style='visual',
            preferred_difficulty='advanced',
            academic_goals='Achieve Excellence, prepare for university',
            interests='["mathematics", "physics", "competitive programming"]',
            attendance_rate=95.0,
            is_active=True
        )
        
        # Create Jordan - Average Learner
        jordan = User(
            role='student',
            first_name='Jordan',
            last_name='Simulated',
            year_level='Year 12',
            learning_style='reading',
            preferred_difficulty='intermediate',
            academic_goals='Improve grades steadily, build confidence',
            interests='["sports", "music", "art"]',
            attendance_rate=85.0,
            is_active=True
        )
        
        # Create Taylor - Struggling Student
        taylor = User(
            role='student',
            first_name='Taylor',
            last_name='Simulated',
            year_level='Year 12',
            learning_style='kinesthetic',
            preferred_difficulty='beginner',
            academic_goals='Understand core concepts, pass exams',
            interests='["gaming", "movies", "socializing"]',
            attendance_rate=75.0,
            learning_difficulty='Attention difficulties',
            is_active=True
        )
        
        # Add to database
        db.session.add(alex)
        db.session.add(jordan)
        db.session.add(taylor)
        db.session.commit()
        
        # Enroll in test class
        test_class.users.append(alex)
        test_class.users.append(jordan)
        test_class.users.append(taylor)
        db.session.commit()
        
        print(f"✅ Created 3 simulated students:")
        print(f"   - Alex (High Performer) - ID: {alex.id}")
        print(f"   - Jordan (Average Learner) - ID: {jordan.id}")
        print(f"   - Taylor (Struggling) - ID: {taylor.id}")
        print(f"✅ Enrolled in: {test_class.name} (ID: {test_class.id})")
        
        return alex.id, jordan.id, taylor.id

if __name__ == '__main__':
    create_simulated_students()
