from app import db
from models import User, Class, Assignment, AssignmentSubmission, Grade, AIModel, ChatMessage, StudentProfile, ContentFile
from auth import hash_password
from datetime import datetime, timedelta
import json
import random

def init_dummy_users():
    """Initialize comprehensive dummy users for testing"""
    
    # Admin users
    admin_users = [
        {
            'email': 'admin@admin.com',
            'password': 'admin123',
            'role': 'admin',
            'first_name': 'Admin',
            'last_name': 'User'
        }
    ]
    
    # Teacher users
    teacher_users = [
        {
            'email': 'teacher@teacher.com',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Sarah',
            'last_name': 'Smith'
        },
        {
            'email': 'john.doe@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'John',
            'last_name': 'Doe'
        },
        {
            'email': 'maria.garcia@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Maria',
            'last_name': 'Garcia'
        },
        {
            'email': 'david.brown@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'David',
            'last_name': 'Brown'
        },
        {
            'email': 'lisa.chen@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Lisa',
            'last_name': 'Chen'
        },
        {
            'email': 'michael.wilson@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Michael',
            'last_name': 'Wilson'
        },
        {
            'email': 'jennifer.lee@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Jennifer',
            'last_name': 'Lee'
        },
        {
            'email': 'robert.taylor@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Robert',
            'last_name': 'Taylor'
        },
        {
            'email': 'amanda.white@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Amanda',
            'last_name': 'White'
        },
        {
            'email': 'carlos.rodriguez@school.edu',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Carlos',
            'last_name': 'Rodriguez'
        }
    ]
    
    # Student users with detailed profiles
    student_users = [
        {
            'email': 'student@student.com',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Emily',
            'last_name': 'Johnson',
            'age': 16,
            'learning_style': 'visual',
            'interests': ['mathematics', 'computer science', 'art'],
            'academic_goals': 'Improve math skills and explore programming',
            'preferred_difficulty': 'intermediate'
        },
        {
            'email': 'alex.martin@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Alex',
            'last_name': 'Martin',
            'age': 17,
            'learning_style': 'kinesthetic',
            'interests': ['science', 'sports', 'music'],
            'academic_goals': 'Excel in chemistry and biology',
            'preferred_difficulty': 'advanced'
        },
        {
            'email': 'sophie.davis@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Sophie',
            'last_name': 'Davis',
            'age': 15,
            'learning_style': 'auditory',
            'interests': ['literature', 'history', 'languages'],
            'academic_goals': 'Improve writing and communication skills',
            'preferred_difficulty': 'beginner'
        },
        {
            'email': 'jacob.miller@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Jacob',
            'last_name': 'Miller',
            'age': 16,
            'learning_style': 'reading',
            'interests': ['physics', 'engineering', 'robotics'],
            'academic_goals': 'Master physics concepts and build projects',
            'preferred_difficulty': 'advanced'
        },
        {
            'email': 'maya.patel@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Maya',
            'last_name': 'Patel',
            'age': 17,
            'learning_style': 'visual',
            'interests': ['art', 'design', 'photography'],
            'academic_goals': 'Develop creative skills and portfolio',
            'preferred_difficulty': 'intermediate'
        },
        {
            'email': 'ethan.thomas@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Ethan',
            'last_name': 'Thomas',
            'age': 15,
            'learning_style': 'kinesthetic',
            'interests': ['mathematics', 'statistics', 'economics'],
            'academic_goals': 'Understand advanced mathematics',
            'preferred_difficulty': 'intermediate'
        },
        {
            'email': 'olivia.anderson@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Olivia',
            'last_name': 'Anderson',
            'age': 16,
            'learning_style': 'auditory',
            'interests': ['biology', 'environmental science', 'chemistry'],
            'academic_goals': 'Pursue career in environmental science',
            'preferred_difficulty': 'advanced'
        },
        {
            'email': 'noah.jackson@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Noah',
            'last_name': 'Jackson',
            'age': 17,
            'learning_style': 'reading',
            'interests': ['history', 'politics', 'debate'],
            'academic_goals': 'Improve analytical and debate skills',
            'preferred_difficulty': 'intermediate'
        },
        {
            'email': 'ava.harris@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Ava',
            'last_name': 'Harris',
            'age': 15,
            'learning_style': 'visual',
            'interests': ['psychology', 'sociology', 'counseling'],
            'academic_goals': 'Understand human behavior and social dynamics',
            'preferred_difficulty': 'beginner'
        },
        {
            'email': 'liam.clark@student.edu',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Liam',
            'last_name': 'Clark',
            'age': 16,
            'learning_style': 'kinesthetic',
            'interests': ['computer science', 'gaming', 'programming'],
            'academic_goals': 'Learn software development and game design',
            'preferred_difficulty': 'advanced'
        }
    ]
    
    all_users = admin_users + teacher_users + student_users
    
    for user_data in all_users:
        # Check if user already exists
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(
                email=user_data['email'],
                password_hash=hash_password(user_data['password']),
                role=user_data['role'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                age=user_data.get('age'),
                learning_style=user_data.get('learning_style'),
                interests=json.dumps(user_data.get('interests', [])),
                academic_goals=user_data.get('academic_goals'),
                preferred_difficulty=user_data.get('preferred_difficulty')
            )
            db.session.add(user)
    
    try:
        db.session.commit()
        print("Dummy users initialized successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing dummy users: {e}")

def init_ai_models():
    """Initialize AI models for different subjects"""
    ai_models = [
        {
            'subject': 'mathematics',
            'model_name': 'gpt-4o',
            'prompt_template': 'You are a mathematics tutor. Help students understand mathematical concepts step by step. Consider their learning style and difficulty preference.',
            'max_tokens': 1000,
            'temperature': 0.3
        },
        {
            'subject': 'science',
            'model_name': 'gpt-4o',
            'prompt_template': 'You are a science tutor specializing in physics, chemistry, and biology. Explain concepts clearly and provide practical examples.',
            'max_tokens': 1200,
            'temperature': 0.4
        },
        {
            'subject': 'english',
            'model_name': 'gpt-4o',
            'prompt_template': 'You are an English literature and writing tutor. Help students improve their writing skills and understand literary works.',
            'max_tokens': 1500,
            'temperature': 0.6
        },
        {
            'subject': 'history',
            'model_name': 'gpt-4o',
            'prompt_template': 'You are a history tutor. Help students understand historical events, their causes, and consequences.',
            'max_tokens': 1300,
            'temperature': 0.5
        },
        {
            'subject': 'art',
            'model_name': 'gpt-4o',
            'prompt_template': 'You are an art tutor. Help students explore creativity, art techniques, and art history.',
            'max_tokens': 1000,
            'temperature': 0.7
        }
    ]
    
    for model_data in ai_models:
        existing_model = AIModel.query.filter_by(subject=model_data['subject']).first()
        if not existing_model:
            ai_model = AIModel(
                subject=model_data['subject'],
                model_name=model_data['model_name'],
                prompt_template=model_data['prompt_template'],
                max_tokens=model_data['max_tokens'],
                temperature=model_data['temperature']
            )
            db.session.add(ai_model)
    
    try:
        db.session.commit()
        print("AI models initialized successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing AI models: {e}")

def init_dummy_classes():
    """Initialize comprehensive dummy classes with AI models"""
    try:
        # Get teachers
        teachers = User.query.filter_by(role='teacher').all()
        students = User.query.filter_by(role='student').all()
        ai_models = AIModel.query.all()
        
        if not teachers or not students:
            print("Teachers or students not found, skipping class initialization")
            return
        
        # Create comprehensive classes
        dummy_classes = [
            {
                'name': 'Advanced Mathematics',
                'description': 'Calculus, trigonometry, and advanced algebra',
                'subject': 'mathematics',
                'teacher_email': 'teacher@teacher.com'
            },
            {
                'name': 'Physics I',
                'description': 'Mechanics, thermodynamics, and wave physics',
                'subject': 'science',
                'teacher_email': 'john.doe@school.edu'
            },
            {
                'name': 'Chemistry Fundamentals',
                'description': 'Atomic structure, chemical bonding, and reactions',
                'subject': 'science',
                'teacher_email': 'maria.garcia@school.edu'
            },
            {
                'name': 'English Literature',
                'description': 'Classic and contemporary literature analysis',
                'subject': 'english',
                'teacher_email': 'david.brown@school.edu'
            },
            {
                'name': 'Creative Writing',
                'description': 'Fiction, poetry, and essay writing techniques',
                'subject': 'english',
                'teacher_email': 'lisa.chen@school.edu'
            },
            {
                'name': 'World History',
                'description': 'Ancient civilizations to modern times',
                'subject': 'history',
                'teacher_email': 'michael.wilson@school.edu'
            },
            {
                'name': 'Art History',
                'description': 'Western and Eastern art movements',
                'subject': 'art',
                'teacher_email': 'jennifer.lee@school.edu'
            },
            {
                'name': 'Biology I',
                'description': 'Cell biology, genetics, and ecology',
                'subject': 'science',
                'teacher_email': 'robert.taylor@school.edu'
            },
            {
                'name': 'Statistics',
                'description': 'Data analysis and probability theory',
                'subject': 'mathematics',
                'teacher_email': 'amanda.white@school.edu'
            },
            {
                'name': 'Studio Art',
                'description': 'Drawing, painting, and sculpture techniques',
                'subject': 'art',
                'teacher_email': 'carlos.rodriguez@school.edu'
            }
        ]
        
        for class_data in dummy_classes:
            existing_class = Class.query.filter_by(name=class_data['name']).first()
            if not existing_class:
                # Find teacher
                teacher = User.query.filter_by(email=class_data['teacher_email']).first()
                if not teacher:
                    continue
                
                # Find corresponding AI model
                ai_model = AIModel.query.filter_by(subject=class_data['subject']).first()
                
                new_class = Class(
                    name=class_data['name'],
                    description=class_data['description'],
                    subject=class_data['subject'],
                    teacher_id=teacher.id,
                    ai_model_id=ai_model.id if ai_model else None
                )
                
                # Add random students to each class (3-7 students per class)
                class_students = random.sample(students, random.randint(3, min(7, len(students))))
                for student in class_students:
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

def init_sample_chat_history():
    """Initialize sample chat history for testing"""
    try:
        students = User.query.filter_by(role='student').all()
        classes = Class.query.all()
        
        sample_messages = [
            "Can you help me understand quadratic equations?",
            "What is the difference between photosynthesis and cellular respiration?",
            "How do I analyze this poem for literary devices?",
            "I'm struggling with calculus derivatives, can you explain step by step?",
            "What caused World War I?",
            "Can you help me with my essay introduction?",
            "I don't understand chemical bonding",
            "How do I solve this physics problem about momentum?",
            "What are the key themes in this novel?",
            "Can you explain how DNA replication works?"
        ]
        
        sample_responses = [
            "I'd be happy to help you with quadratic equations! Let's start with the basic form: ax² + bx + c = 0...",
            "Great question! Photosynthesis and cellular respiration are complementary processes...",
            "When analyzing poetry for literary devices, look for metaphors, similes, alliteration...",
            "Derivatives can be tricky at first. Let's break it down step by step...",
            "World War I had multiple complex causes, including nationalism, imperialism...",
            "A strong essay introduction should hook the reader and clearly state your thesis...",
            "Chemical bonding is fundamental to chemistry. There are three main types...",
            "Physics problems about momentum require understanding the conservation principle...",
            "This novel explores several key themes including identity, belonging, and growth...",
            "DNA replication is a fascinating process that ensures genetic information is passed on..."
        ]
        
        for student in students[:5]:  # Only add chat history for first 5 students
            student_classes = [cls for cls in classes if student in cls.users]
            for class_obj in student_classes[:2]:  # 2 classes per student
                if class_obj.ai_model:
                    # Add 3-5 chat messages per class
                    for i in range(random.randint(3, 5)):
                        message = random.choice(sample_messages)
                        response = random.choice(sample_responses)
                        
                        chat_message = ChatMessage(
                            user_id=student.id,
                            class_id=class_obj.id,
                            ai_model_id=class_obj.ai_model.id,
                            message=message,
                            response=response,
                            message_type='student',
                            context_data=json.dumps({
                                'student_level': student.preferred_difficulty,
                                'learning_style': student.learning_style,
                                'subject': class_obj.subject
                            }),
                            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                        )
                        db.session.add(chat_message)
        
        db.session.commit()
        print("Sample chat history initialized successfully.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing sample chat history: {e}")

def init_student_profiles():
    """Initialize student profiles for AI personalization"""
    try:
        students = User.query.filter_by(role='student').all()
        
        for student in students:
            existing_profile = StudentProfile.query.filter_by(user_id=student.id).first()
            if not existing_profile:
                profile = StudentProfile(
                    user_id=student.id,
                    learning_preferences=json.dumps({
                        'preferred_time': random.choice(['morning', 'afternoon', 'evening']),
                        'study_duration': random.randint(30, 120),
                        'break_frequency': random.randint(15, 45)
                    }),
                    study_patterns=json.dumps({
                        'most_active_subject': random.choice(['math', 'science', 'english', 'history']),
                        'average_session_length': random.randint(45, 90),
                        'preferred_difficulty_progression': random.choice(['gradual', 'quick', 'mixed'])
                    }),
                    performance_metrics=json.dumps({
                        'average_grade': round(random.uniform(70, 95), 2),
                        'improvement_rate': round(random.uniform(0.5, 2.0), 2),
                        'engagement_score': round(random.uniform(6.0, 10.0), 1)
                    }),
                    ai_interaction_history=json.dumps({
                        'total_interactions': random.randint(10, 50),
                        'favorite_topics': random.sample(['algebra', 'chemistry', 'literature', 'history', 'physics'], 3),
                        'help_seeking_frequency': random.choice(['low', 'medium', 'high'])
                    })
                )
                db.session.add(profile)
        
        db.session.commit()
        print("Student profiles initialized successfully.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing student profiles: {e}")
