"""
Student generator with latent traits.
Generates realistic student profiles with learning characteristics.
"""

import random
import json
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple


class StudentGenerator:
    """Generate realistic student profiles with latent traits."""
    
    FIRST_NAMES = [
        'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Ethan', 'Sophia', 'Mason',
        'Isabella', 'William', 'Mia', 'James', 'Charlotte', 'Benjamin', 'Amelia',
        'Lucas', 'Harper', 'Henry', 'Evelyn', 'Alexander', 'Aria', 'Michael',
        'Luna', 'Daniel', 'Chloe', 'Matthew', 'Penelope', 'Aiden', 'Layla',
        'Joseph', 'Riley', 'Jackson', 'Zoey', 'Sebastian', 'Nora', 'David',
        'Lily', 'Carter', 'Eleanor', 'Wyatt', 'Hannah', 'Jayden', 'Lillian',
        'John', 'Addison', 'Owen', 'Aubrey', 'Dylan', 'Ellie', 'Luke'
    ]
    
    LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
        'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
        'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
        'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
        'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King',
        'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green'
    ]
    
    LEARNING_STYLES = ['visual', 'auditory', 'kinesthetic', 'reading']
    YEAR_LEVELS = ['Year 9', 'Year 10', 'Year 11', 'Year 12', 'Year 13']
    ETHNICITIES = ['European', 'Māori', 'Pasifika', 'Asian', 'Middle Eastern', 'Other']
    GENDERS = ['Male', 'Female', 'Other']
    DIFFICULTIES = ['beginner', 'intermediate', 'advanced']
    
    LEARNING_DIFFICULTIES = [
        None, None, None, None, None,
        'Dyslexia', 'ADHD', 'Autism Spectrum', 'Dyscalculia'
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize student generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_latent_traits(self) -> Dict:
        """
        Generate latent student traits that determine behavior.
        
        Returns:
            Dictionary of latent traits
        """
        baseline_ability = np.clip(np.random.normal(0.6, 0.15), 0.2, 0.95)
        learning_rate = np.clip(np.random.normal(0.05, 0.02), 0.01, 0.15)
        engagement_tendency = np.clip(np.random.normal(0.6, 0.2), 0.2, 0.95)
        consistency = np.clip(np.random.normal(0.7, 0.15), 0.3, 0.95)
        help_seeking = np.clip(np.random.normal(0.5, 0.2), 0.1, 0.9)
        
        skill_strengths = {}
        skill_weaknesses = {}
        
        subjects = ['algebra', 'geometry', 'statistics', 'calculus', 'arithmetic']
        n_strengths = random.randint(1, 2)
        n_weaknesses = random.randint(1, 2)
        
        strengths = random.sample(subjects, n_strengths)
        remaining = [s for s in subjects if s not in strengths]
        weaknesses = random.sample(remaining, min(n_weaknesses, len(remaining)))
        
        for s in strengths:
            skill_strengths[s] = random.uniform(0.1, 0.25)
        for w in weaknesses:
            skill_weaknesses[w] = random.uniform(-0.25, -0.1)
        
        strategy_sensitivities = {
            'step_by_step': random.uniform(-0.1, 0.3),
            'worked_example': random.uniform(-0.1, 0.3),
            'socratic': random.uniform(-0.1, 0.3),
            'scaffolding': random.uniform(-0.1, 0.3),
            'analogy': random.uniform(-0.1, 0.3),
            'visual': random.uniform(-0.1, 0.3),
            'chunking': random.uniform(-0.1, 0.3),
            'spaced_retrieval': random.uniform(-0.1, 0.3),
            'elaboration': random.uniform(-0.1, 0.3),
            'quick_check': random.uniform(-0.1, 0.3),
        }
        
        return {
            'baseline_ability': float(baseline_ability),
            'learning_rate': float(learning_rate),
            'engagement_tendency': float(engagement_tendency),
            'consistency': float(consistency),
            'help_seeking': float(help_seeking),
            'skill_strengths': skill_strengths,
            'skill_weaknesses': skill_weaknesses,
            'strategy_sensitivities': strategy_sensitivities,
            'dropout_risk': random.uniform(0.0, 0.3),
            'session_variance': random.uniform(0.1, 0.4)
        }
    
    def generate_student(self, class_id: int, 
                         subject: str = 'math') -> Dict:
        """
        Generate a complete student profile.
        
        Args:
            class_id: Class ID to assign student to
            subject: Subject area
            
        Returns:
            Dictionary with student data
        """
        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        
        year_level = random.choice(self.YEAR_LEVELS)
        year_num = int(year_level.split()[-1])
        base_age = year_num + 4
        age = base_age + random.randint(-1, 1)
        
        birth_year = date.today().year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        dob = date(birth_year, birth_month, birth_day)
        
        latent_traits = self.generate_latent_traits()
        
        if latent_traits['baseline_ability'] > 0.7:
            preferred_difficulty = 'advanced'
        elif latent_traits['baseline_ability'] < 0.4:
            preferred_difficulty = 'beginner'
        else:
            preferred_difficulty = 'intermediate'
        
        attendance = np.clip(
            np.random.normal(0.9, 0.1) - latent_traits['dropout_risk'] * 0.3,
            0.5, 1.0
        )
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'role': 'student',
            'age': age,
            'gender': random.choice(self.GENDERS),
            'ethnicity': random.choice(self.ETHNICITIES),
            'date_of_birth': dob,
            'year_level': year_level,
            'primary_language': 'English',
            'secondary_language': random.choice([None, None, None, 'Māori', 'Spanish', 'Mandarin']),
            'learning_difficulty': random.choice(self.LEARNING_DIFFICULTIES),
            'extracurricular_activities': json.dumps(self._generate_activities()),
            'major_life_event': random.choice([None, None, None, None, 'Recent family move', 'New sibling']),
            'attendance_rate': float(attendance),
            'learning_style': random.choice(self.LEARNING_STYLES),
            'interests': json.dumps(self._generate_interests(subject)),
            'academic_goals': self._generate_goals(year_level, subject),
            'preferred_difficulty': preferred_difficulty,
            'is_active': True,
            'class_id': class_id,
            'latent_traits': latent_traits
        }
    
    def _generate_activities(self) -> List[str]:
        """Generate random extracurricular activities."""
        activities = [
            'Soccer', 'Basketball', 'Swimming', 'Music', 'Drama', 'Chess',
            'Debate', 'Art', 'Dance', 'Robotics', 'Coding Club', 'Volunteer Work'
        ]
        n = random.randint(0, 3)
        return random.sample(activities, n)
    
    def _generate_interests(self, subject: str) -> List[str]:
        """Generate student interests."""
        interests = {
            'math': ['Problem solving', 'Puzzles', 'Video games', 'Science'],
            'science': ['Experiments', 'Nature', 'Technology', 'Space'],
            'english': ['Reading', 'Writing', 'Movies', 'Creative stories'],
            'history': ['Documentaries', 'Museums', 'Politics', 'Travel']
        }
        base = interests.get(subject, ['Learning', 'Games'])
        n = random.randint(1, 3)
        return random.sample(base, min(n, len(base)))
    
    def _generate_goals(self, year_level: str, subject: str) -> str:
        """Generate academic goals."""
        goals = [
            f"Improve my {subject} grade this term",
            f"Understand {subject} concepts better",
            f"Get better at solving problems",
            f"Prepare for {year_level} exams",
            f"Build confidence in {subject}"
        ]
        return random.choice(goals)
    
    def generate_batch(self, n_students: int, class_id: int,
                       subject: str = 'math') -> List[Dict]:
        """
        Generate a batch of students.
        
        Args:
            n_students: Number of students to generate
            class_id: Class ID
            subject: Subject area
            
        Returns:
            List of student dictionaries
        """
        return [self.generate_student(class_id, subject) for _ in range(n_students)]
