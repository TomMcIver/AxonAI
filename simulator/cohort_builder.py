"""
Cohort builder for generating complete demo datasets.
Orchestrates student and interaction generation.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .student_generator import StudentGenerator
from .interaction_simulator import InteractionSimulator
from skill_taxonomy import SKILL_TAXONOMY, TEACHING_STRATEGIES


class CohortBuilder:
    """Build complete demo cohorts with students, interactions, and assessments."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize cohort builder.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.student_gen = StudentGenerator(seed)
        self.interaction_sim = InteractionSimulator(seed)
        
        if seed is not None:
            random.seed(seed)
    
    def build_cohort(self, n_students: int = 100,
                     n_classes: int = 3,
                     n_days: int = 30,
                     subject: str = 'math') -> Dict:
        """
        Build a complete demo cohort.
        
        Args:
            n_students: Total number of students
            n_classes: Number of classes
            n_days: Number of days of data to generate
            subject: Subject area
            
        Returns:
            Dictionary with all generated data
        """
        skills = SKILL_TAXONOMY.get(subject, ['general'])
        
        students_per_class = n_students // n_classes
        remaining = n_students % n_classes
        
        classes = []
        all_students = []
        all_interactions = []
        all_quizzes = []
        all_mastery_states = []
        
        for c in range(n_classes):
            class_data = {
                'name': f'{subject.title()} Class {c + 1}',
                'subject': subject,
                'description': f'Demo {subject} class for Year {10 + c}',
                'class_index': c
            }
            classes.append(class_data)
            
            n_class_students = students_per_class + (1 if c < remaining else 0)
            
            for s in range(n_class_students):
                student = self.student_gen.generate_student(c, subject)
                student['student_index'] = len(all_students)
                all_students.append(student)
                
                student_interactions, student_quizzes, mastery_history = self._generate_student_data(
                    student, skills, n_days
                )
                
                for i in student_interactions:
                    i['student_index'] = student['student_index']
                    i['class_index'] = c
                all_interactions.extend(student_interactions)
                
                for q in student_quizzes:
                    q['student_index'] = student['student_index']
                    q['class_index'] = c
                all_quizzes.extend(student_quizzes)
                
                for m in mastery_history:
                    m['student_index'] = student['student_index']
                all_mastery_states.extend(mastery_history)
        
        return {
            'classes': classes,
            'students': all_students,
            'interactions': all_interactions,
            'quizzes': all_quizzes,
            'mastery_states': all_mastery_states,
            'metadata': {
                'n_students': n_students,
                'n_classes': n_classes,
                'n_days': n_days,
                'subject': subject,
                'seed': self.seed,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    def _generate_student_data(self, student: Dict, skills: List[str],
                               n_days: int) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Generate all data for a single student.
        
        Args:
            student: Student data
            skills: Available skills
            n_days: Number of days
            
        Returns:
            Tuple of (interactions, quizzes, mastery_states)
        """
        traits = student.get('latent_traits', {})
        engagement = traits.get('engagement_tendency', 0.5)
        
        n_sessions = int(n_days * engagement * random.uniform(0.3, 0.6))
        n_quizzes = max(1, n_sessions // 5)
        
        start_date = datetime.utcnow() - timedelta(days=n_days)
        
        interactions = []
        mastery_states = []
        
        for skill in skills[:4]:
            if random.random() < 0.4:
                pattern = random.choice(['improvement', 'plateau', 'regression'])
            else:
                pattern = 'improvement'
            
            skill_sessions = int(n_sessions * random.uniform(0.2, 0.5))
            
            if pattern == 'plateau':
                sessions = self.interaction_sim.simulate_plateau(
                    student, skill, n_sessions=skill_sessions
                )
            elif pattern == 'regression':
                sessions = self.interaction_sim.simulate_regression(
                    student, skill, n_sessions=skill_sessions
                )
            else:
                sessions = self.interaction_sim.simulate_improvement_curve(
                    student, skill, n_sessions=skill_sessions, start_date=start_date
                )
            
            for session in sessions:
                session_interactions = self.interaction_sim.simulate_session(
                    student, skill, session['strategy'],
                    n_interactions=session['n_interactions'],
                    start_time=session['date']
                )
                interactions.extend(session_interactions)
                
                mastery_states.append({
                    'skill': skill,
                    'p_mastery': session['mastery_after'],
                    'updated_at': session['date'],
                    'confidence': min(0.9, 0.3 + len(sessions) * 0.1)
                })
        
        quizzes = []
        quiz_interval = n_days // n_quizzes
        
        for i in range(n_quizzes):
            quiz_date = start_date + timedelta(days=(i + 1) * quiz_interval)
            quiz_skills = random.sample(skills, min(3, len(skills)))
            
            quiz = self.interaction_sim.simulate_quiz(
                student, quiz_skills,
                n_questions=len(quiz_skills) * 2,
                test_time=quiz_date
            )
            quizzes.append(quiz)
        
        return interactions, quizzes, mastery_states
    
    def populate_database(self, db, app, cohort_data: Dict,
                          teacher_id: int) -> Dict:
        """
        Populate the database with cohort data.
        
        Args:
            db: SQLAlchemy database instance
            app: Flask app for context
            cohort_data: Generated cohort data
            teacher_id: Teacher user ID
            
        Returns:
            Dictionary mapping indices to database IDs
        """
        from models import (User, Class, AIInteraction, MiniTest, MiniTestResponse,
                           MasteryState, OptimizedProfile, AIModel)
        
        with app.app_context():
            class_map = {}
            student_map = {}
            
            subject = cohort_data['metadata']['subject']
            ai_model = AIModel.query.filter_by(subject=subject).first()
            if not ai_model:
                ai_model = AIModel(
                    subject=subject,
                    model_name='gpt-4o-mini',
                    prompt_template=f'You are an AI tutor for {subject}.',
                    is_active=True
                )
                db.session.add(ai_model)
                db.session.commit()
            
            for class_data in cohort_data['classes']:
                cls = Class(
                    name=class_data['name'],
                    subject=class_data['subject'],
                    description=class_data['description'],
                    teacher_id=teacher_id,
                    ai_model_id=ai_model.id,
                    is_active=True
                )
                db.session.add(cls)
                db.session.flush()
                class_map[class_data['class_index']] = cls.id
            
            for student_data in cohort_data['students']:
                latent_traits = student_data.pop('latent_traits', {})
                student_index = student_data.pop('student_index')
                class_id = class_map[student_data.pop('class_id')]
                
                user = User(
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    role='student',
                    age=student_data.get('age'),
                    gender=student_data.get('gender'),
                    ethnicity=student_data.get('ethnicity'),
                    date_of_birth=student_data.get('date_of_birth'),
                    year_level=student_data.get('year_level'),
                    primary_language=student_data.get('primary_language'),
                    secondary_language=student_data.get('secondary_language'),
                    learning_difficulty=student_data.get('learning_difficulty'),
                    extracurricular_activities=student_data.get('extracurricular_activities'),
                    major_life_event=student_data.get('major_life_event'),
                    attendance_rate=student_data.get('attendance_rate'),
                    learning_style=student_data.get('learning_style'),
                    interests=student_data.get('interests'),
                    academic_goals=student_data.get('academic_goals'),
                    preferred_difficulty=student_data.get('preferred_difficulty'),
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                cls = Class.query.get(class_id)
                if cls:
                    cls.users.append(user)
                
                student_map[student_index] = user.id
                
                profile = OptimizedProfile(
                    user_id=user.id,
                    current_pass_rate=latent_traits.get('baseline_ability', 0.5) * 100,
                    engagement_level=latent_traits.get('engagement_tendency', 0.5),
                    mastery_scores=json.dumps({}),
                    strategy_success_rates=json.dumps(latent_traits.get('strategy_sensitivities', {}))
                )
                db.session.add(profile)
            
            db.session.commit()
            
            for interaction in cohort_data['interactions']:
                student_id = student_map.get(interaction['student_index'])
                class_id = class_map.get(interaction['class_index'])
                
                if student_id and class_id:
                    ai_interaction = AIInteraction(
                        user_id=student_id,
                        class_id=class_id,
                        ai_model_id=ai_model.id,
                        prompt=interaction['prompt'],
                        response=interaction['response'],
                        strategy_used=interaction.get('strategy_used'),
                        sub_topic=interaction.get('sub_topic'),
                        engagement_score=interaction.get('engagement_score'),
                        success_indicator=interaction.get('success_indicator'),
                        tokens_in=len(interaction['prompt'].split()) * 2,
                        tokens_out=len(interaction['response'].split()) * 2,
                        response_time_ms=interaction.get('response_time_ms', 1000),
                        context_data=interaction.get('context_data'),
                        created_at=interaction['created_at']
                    )
                    db.session.add(ai_interaction)
            
            for mastery in cohort_data['mastery_states']:
                student_id = student_map.get(mastery['student_index'])
                if student_id:
                    state = MasteryState(
                        student_id=student_id,
                        skill=mastery['skill'],
                        p_mastery=mastery['p_mastery'],
                        confidence=mastery.get('confidence', 0.5),
                        updated_at=mastery['updated_at'],
                        model_version='v1'
                    )
                    db.session.add(state)
            
            db.session.commit()
            
            return {
                'class_map': class_map,
                'student_map': student_map,
                'n_interactions': len(cohort_data['interactions']),
                'n_mastery_states': len(cohort_data['mastery_states'])
            }
