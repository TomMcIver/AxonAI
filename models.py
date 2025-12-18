from app import db
from datetime import datetime
import json

# Association table for many-to-many relationship between users and classes
class_users = db.Table('class_users',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    photo_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Enhanced student profile fields for AI personalization
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # Male, Female, Other
    ethnicity = db.Column(db.String(100), nullable=True)  # European, Māori, Pasifika, Asian, etc.
    date_of_birth = db.Column(db.Date, nullable=True)
    year_level = db.Column(db.String(20), nullable=True)  # Year 11, Year 12, Year 13
    primary_language = db.Column(db.String(50), nullable=True)
    secondary_language = db.Column(db.String(50), nullable=True)
    learning_difficulty = db.Column(db.String(100), nullable=True)  # Dyslexia, ADHD, etc.
    extracurricular_activities = db.Column(db.Text, nullable=True)  # JSON string
    major_life_event = db.Column(db.String(200), nullable=True)
    attendance_rate = db.Column(db.Float, nullable=True)  # Average attendance percentage
    
    # Original AI fields
    learning_style = db.Column(db.String(50), nullable=True)  # visual, auditory, kinesthetic, reading
    interests = db.Column(db.Text, nullable=True)  # JSON string of interests
    academic_goals = db.Column(db.Text, nullable=True)
    preferred_difficulty = db.Column(db.String(20), nullable=True)  # beginner, intermediate, advanced
    
    # Relationships
    classes = db.relationship('Class', secondary=class_users, back_populates='users')
    submitted_assignments = db.relationship('AssignmentSubmission', back_populates='student')
    grades = db.relationship('Grade', foreign_keys='Grade.student_id', back_populates='student')
    chat_messages = db.relationship('ChatMessage', back_populates='user')

    def __repr__(self):
        return f'<User {self.get_full_name()} - {self.role}>'

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_average_grade(self):
        """Calculate overall average grade for student"""
        if self.role != 'student':
            return None
        
        grades = [g.grade for g in self.grades if g.grade is not None]
        if not grades:
            return None
        return sum(grades) / len(grades)

    def get_class_average(self, class_id):
        """Get average grade for a specific class"""
        if self.role != 'student':
            return None
            
        class_grades = [g.grade for g in self.grades if g.assignment.class_id == class_id and g.grade is not None]
        if not class_grades:
            return None
        return sum(class_grades) / len(class_grades)

    def get_interests_list(self):
        """Get interests as a list"""
        if not self.interests:
            return []
        try:
            return json.loads(self.interests)
        except:
            return []
    
    def set_interests_list(self, interests_list):
        """Set interests from a list"""
        self.interests = json.dumps(interests_list)
    
    def get_extracurricular_list(self):
        """Get extracurricular activities as a list"""
        if not self.extracurricular_activities:
            return []
        try:
            return json.loads(self.extracurricular_activities)
        except:
            return []
    
    def set_extracurricular_list(self, activities_list):
        """Set extracurricular activities from a list"""
        self.extracurricular_activities = json.dumps(activities_list)
    
    def get_ai_profile_summary(self):
        """Generate a concise AI profile summary for token optimization"""
        summary = f"Student: {self.first_name} ({self.year_level or 'Unknown year'})"
        
        if self.gender:
            summary += f", {self.gender}"
        if self.ethnicity:
            summary += f", {self.ethnicity}"
        
        if self.learning_style:
            summary += f"\nLearning: {self.learning_style} learner"
        if self.preferred_difficulty:
            summary += f", {self.preferred_difficulty} level"
        
        if self.learning_difficulty:
            summary += f"\nSpecial needs: {self.learning_difficulty}"
        
        avg_grade = self.get_average_grade()
        if avg_grade:
            trend = "improving" if avg_grade > 70 else "stable" if avg_grade > 60 else "needs support"
            summary += f"\nPerformance: Grade average {avg_grade:.1f}%, trend {trend}"
        
        if self.academic_goals:
            summary += f"\nGoals: {self.academic_goals[:100]}..."
        
        activities = self.get_extracurricular_list()
        if activities:
            summary += f"\nActivities: {', '.join(activities[:3])}"
        
        if self.major_life_event:
            summary += f"\nContext: {self.major_life_event}"
        
        return summary
    
    def get_chat_summary(self, class_id=None):
        """Get a summary of chat interactions for AI context"""
        messages = self.chat_messages
        if class_id:
            messages = [msg for msg in messages if msg.class_id == class_id]
        
        return {
            'total_messages': len(messages),
            'recent_topics': [msg.message[:50] for msg in messages[-5:]] if messages else [],
            'engagement_level': 'high' if len(messages) > 20 else 'medium' if len(messages) > 5 else 'low'
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'photo_url': self.photo_url,
            'age': self.age,
            'gender': self.gender,
            'ethnicity': self.ethnicity,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'year_level': self.year_level,
            'primary_language': self.primary_language,
            'secondary_language': self.secondary_language,
            'learning_difficulty': self.learning_difficulty,
            'extracurricular_activities': self.get_extracurricular_list(),
            'major_life_event': self.major_life_event,
            'attendance_rate': self.attendance_rate,
            'learning_style': self.learning_style,
            'interests': self.get_interests_list(),
            'academic_goals': self.academic_goals,
            'preferred_difficulty': self.preferred_difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(50), nullable=True)  # math, science, english, etc.
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ai_model_id = db.Column(db.Integer, db.ForeignKey('ai_model.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    users = db.relationship('User', secondary=class_users, back_populates='classes')
    assignments = db.relationship('Assignment', back_populates='class_obj')
    content_files = db.relationship('ContentFile', back_populates='class_obj')
    ai_model = db.relationship('AIModel', back_populates='classes')
    chat_messages = db.relationship('ChatMessage', back_populates='class_obj')

    def __repr__(self):
        return f'<Class {self.name}>'

    def get_students(self):
        """Get all students in this class"""
        return [user for user in self.users if user.role == 'student']

    def get_student_count(self):
        """Get count of students in this class"""
        return len(self.get_students())

    def get_pass_rate(self):
        """Calculate pass rate for this class (grades >= 60)"""
        students = self.get_students()
        if not students:
            return 0
        
        passed_count = 0
        for student in students:
            avg_grade = student.get_class_average(self.id)
            if avg_grade is not None and avg_grade >= 60:
                passed_count += 1
        
        return (passed_count / len(students)) * 100

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    max_points = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    class_obj = db.relationship('Class', back_populates='assignments')
    submissions = db.relationship('AssignmentSubmission', back_populates='assignment')
    grades = db.relationship('Grade', back_populates='assignment')

    def __repr__(self):
        return f'<Assignment {self.title}>'

    def get_submission_by_student(self, student_id):
        """Get submission for this assignment by a specific student"""
        return AssignmentSubmission.query.filter_by(
            assignment_id=self.id,
            student_id=student_id
        ).first()

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(200), nullable=True)
    file_name = db.Column(db.String(200), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignment = db.relationship('Assignment', back_populates='submissions')
    student = db.relationship('User', back_populates='submitted_assignments')
    grade = db.relationship('Grade', back_populates='submission', uselist=False)

    def __repr__(self):
        return f'<AssignmentSubmission {self.id}>'

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('assignment_submission.id'), nullable=True)
    grade = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    assignment = db.relationship('Assignment', back_populates='grades')
    student = db.relationship('User', foreign_keys=[student_id], back_populates='grades')
    submission = db.relationship('AssignmentSubmission', back_populates='grade')
    teacher = db.relationship('User', foreign_keys=[graded_by])

    def __repr__(self):
        return f'<Grade {self.grade}>'

class ContentFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, txt, slides
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = db.relationship('Class', back_populates='content_files')
    uploader = db.relationship('User')

    def __repr__(self):
        return f'<ContentFile {self.name}>'

# AI Chatbot Models
class AIModel(db.Model):
    """Fine-tuned AI models for each class subject"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)  # math, science, english, etc.
    model_name = db.Column(db.String(200), nullable=False)  # OpenAI model identifier
    fine_tuned_id = db.Column(db.String(200), nullable=True)  # Fine-tuned model ID
    prompt_template = db.Column(db.Text, nullable=True)  # System prompt template
    max_tokens = db.Column(db.Integer, default=1000)
    temperature = db.Column(db.Float, default=0.7)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    classes = db.relationship('Class', back_populates='ai_model')
    chat_messages = db.relationship('ChatMessage', back_populates='ai_model')
    
    def __repr__(self):
        return f'<AIModel {self.subject}>'

class ChatMessage(db.Model):
    """Chat history between students and AI models"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    ai_model_id = db.Column(db.Integer, db.ForeignKey('ai_model.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # student, teacher, system
    context_data = db.Column(db.Text, nullable=True)  # JSON string of additional context
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='chat_messages')
    class_obj = db.relationship('Class', back_populates='chat_messages')
    ai_model = db.relationship('AIModel', back_populates='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'class_id': self.class_id,
            'ai_model_id': self.ai_model_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'context_data': json.loads(self.context_data) if self.context_data else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TokenUsage(db.Model):
    """Track AI token usage per user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)
    requests_made = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='token_usage')
    
    def __repr__(self):
        return f'<TokenUsage {self.user_id} - {self.date}: {self.tokens_used} tokens>'

class StudentProfile(db.Model):
    """Extended student profile for AI personalization"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    learning_preferences = db.Column(db.Text, nullable=True)  # JSON string
    study_patterns = db.Column(db.Text, nullable=True)  # JSON string
    performance_metrics = db.Column(db.Text, nullable=True)  # JSON string
    ai_interaction_history = db.Column(db.Text, nullable=True)  # JSON string
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='student_profile')
    
    def __repr__(self):
        return f'<StudentProfile {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'learning_preferences': json.loads(self.learning_preferences) if self.learning_preferences else None,
            'study_patterns': json.loads(self.study_patterns) if self.study_patterns else None,
            'performance_metrics': json.loads(self.performance_metrics) if self.performance_metrics else None,
            'ai_interaction_history': json.loads(self.ai_interaction_history) if self.ai_interaction_history else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class AIInteraction(db.Model):
    """Detailed AI interaction tracking for Individual AI Tutors"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    ai_model_id = db.Column(db.Integer, db.ForeignKey('ai_model.id'), nullable=False)
    
    # Interaction details
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    strategy_used = db.Column(db.String(100), nullable=True)  # teaching_strategy
    sub_topic = db.Column(db.String(50), nullable=True)  # algebra, statistics, calculus
    engagement_score = db.Column(db.Float, nullable=True)  # 0-1 engagement level
    
    # Performance metrics
    tokens_in = db.Column(db.Integer, nullable=False)
    tokens_out = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    
    # Learning outcomes
    success_indicator = db.Column(db.Boolean, nullable=True)  # Did strategy work?
    user_feedback = db.Column(db.Integer, nullable=True)  # 1-5 rating
    linked_assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=True)
    linked_content_id = db.Column(db.Integer, db.ForeignKey('content_file.id'), nullable=True)
    
    # Misconception diagnosis fields (P3)
    misconception_tags = db.Column(db.Text, nullable=True)  # JSON array of misconception identifiers
    reasoning_gap = db.Column(db.Text, nullable=True)  # Description of student's reasoning gap
    next_step_recommendation = db.Column(db.Text, nullable=True)  # Recommended next learning step
    
    # Context data
    context_data = db.Column(db.Text, nullable=True)  # JSON: mood, time_of_day, etc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_interactions')
    class_obj = db.relationship('Class', backref='ai_interactions')
    ai_model = db.relationship('AIModel', backref='interactions')
    assignment = db.relationship('Assignment', backref='ai_interactions')
    content_file = db.relationship('ContentFile', backref='ai_interactions')
    
    def __repr__(self):
        return f'<AIInteraction {self.id}: User {self.user_id}>'

class FailedStrategy(db.Model):
    """Log of teaching strategies that didn't work for specific students"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    strategy_name = db.Column(db.String(100), nullable=False)
    failure_reason = db.Column(db.Text, nullable=True)  # Why it failed
    failure_count = db.Column(db.Integer, default=1)
    last_attempted = db.Column(db.DateTime, default=datetime.utcnow)
    context_data = db.Column(db.Text, nullable=True)  # JSON: topic, difficulty, etc
    
    # Relationships
    user = db.relationship('User', backref='failed_strategies')
    class_obj = db.relationship('Class', backref='failed_strategies')
    
    def __repr__(self):
        return f'<FailedStrategy {self.strategy_name} for User {self.user_id}>'

class OptimizedProfile(db.Model):
    """Fast-access optimized profile cache for real-time AI tutoring"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Cached performance metrics
    current_pass_rate = db.Column(db.Float, nullable=True)
    predicted_pass_rate = db.Column(db.Float, nullable=True)
    engagement_level = db.Column(db.Float, nullable=True)  # 0-1
    mastery_scores = db.Column(db.Text, nullable=True)  # JSON: {skill: score}
    
    # Learning patterns
    best_time_of_day = db.Column(db.String(20), nullable=True)  # morning/afternoon/evening
    optimal_session_length = db.Column(db.Integer, nullable=True)  # minutes
    preferred_strategies = db.Column(db.Text, nullable=True)  # JSON array
    avoided_strategies = db.Column(db.Text, nullable=True)  # JSON array
    
    # Quick access data
    recent_topics = db.Column(db.Text, nullable=True)  # JSON array
    struggle_areas = db.Column(db.Text, nullable=True)  # JSON array
    strength_areas = db.Column(db.Text, nullable=True)  # JSON array
    
    # Persistent chat counters for quick check triggering
    chat_counters = db.Column(db.Text, nullable=True)  # JSON: {"class_id": count}
    
    # Strategy success tracking for epsilon-greedy bandit (P3)
    # JSON: {"algebra": {"socratic": {"wins": 12, "trials": 20}, ...}, ...}
    strategy_success_rates = db.Column(db.Text, nullable=True)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='optimized_profile', uselist=False)
    
    def __repr__(self):
        return f'<OptimizedProfile User {self.user_id}>'

class MiniTest(db.Model):
    """Adaptive mini-tests generated by AI tutors"""
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    created_by_ai = db.Column(db.Integer, db.ForeignKey('ai_model.id'), nullable=False)
    
    # Test details
    test_type = db.Column(db.String(50), nullable=False)  # quiz, diagnostic, practice
    difficulty_level = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    skills_tested = db.Column(db.Text, nullable=False)  # JSON array
    questions = db.Column(db.Text, nullable=False)  # JSON array of questions
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = db.relationship('Class', backref='mini_tests')
    ai_model = db.relationship('AIModel', backref='generated_tests')
    
    def __repr__(self):
        return f'<MiniTest {self.id}: {self.test_type}>'

class MiniTestResponse(db.Model):
    """Student responses to mini-tests"""
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('mini_test.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    answers = db.Column(db.Text, nullable=False)  # JSON array
    score = db.Column(db.Float, nullable=False)  # percentage
    time_taken = db.Column(db.Integer, nullable=True)  # seconds
    skill_scores = db.Column(db.Text, nullable=True)  # JSON: {skill: score}
    
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test = db.relationship('MiniTest', backref='responses')
    user = db.relationship('User', backref='test_responses')
    
    def __repr__(self):
        return f'<MiniTestResponse Test {self.test_id} User {self.user_id}>'

class PatternInsight(db.Model):
    """Global patterns discovered by Big AI Coordinator"""
    id = db.Column(db.Integer, primary_key=True)
    pattern_type = db.Column(db.String(100), nullable=False)  # learning_style, age_group, etc
    pattern_description = db.Column(db.Text, nullable=False)
    
    # Pattern details
    applicable_criteria = db.Column(db.Text, nullable=False)  # JSON: who this applies to
    recommended_strategies = db.Column(db.Text, nullable=False)  # JSON array
    success_rate = db.Column(db.Float, nullable=True)  # effectiveness percentage
    sample_size = db.Column(db.Integer, nullable=False)  # students analyzed
    
    # Metadata
    confidence_level = db.Column(db.Float, nullable=True)  # 0-1
    last_validated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PatternInsight {self.pattern_type}>'

class PredictedGrade(db.Model):
    """AI-predicted grades based on portfolio analysis"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    
    # Predictions
    current_trajectory = db.Column(db.Float, nullable=False)  # current grade path
    predicted_final_grade = db.Column(db.Float, nullable=False)  # predicted outcome
    confidence_level = db.Column(db.Float, nullable=False)  # 0-1
    
    # Analysis basis
    factors_analyzed = db.Column(db.Text, nullable=False)  # JSON: what went into prediction
    improvement_areas = db.Column(db.Text, nullable=True)  # JSON: where to focus
    risk_factors = db.Column(db.Text, nullable=True)  # JSON: what might hurt grade
    
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='predicted_grades')
    class_obj = db.relationship('Class', backref='predicted_grades')
    
    def __repr__(self):
        return f'<PredictedGrade User {self.user_id} Class {self.class_id}>'

class TeacherAIInsight(db.Model):
    """AI-generated insights and interventions for teachers"""
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Insight details
    insight_type = db.Column(db.String(100), nullable=False)  # at_risk, improving, needs_support
    summary = db.Column(db.Text, nullable=False)  # AI summary of student status
    suggested_interventions = db.Column(db.Text, nullable=False)  # JSON array
    
    # Analysis data
    failed_strategies = db.Column(db.Text, nullable=True)  # JSON: what hasn't worked
    successful_strategies = db.Column(db.Text, nullable=True)  # JSON: what has worked
    engagement_analysis = db.Column(db.Text, nullable=True)  # JSON: engagement patterns
    
    # Action tracking
    viewed_by_teacher = db.Column(db.Boolean, default=False)
    action_taken = db.Column(db.Text, nullable=True)  # Teacher's response
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = db.relationship('Class', backref='teacher_insights')
    student = db.relationship('User', foreign_keys=[student_id], backref='insights_about')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='insights_for')
    
    def __repr__(self):
        return f'<TeacherAIInsight Class {self.class_id} Student {self.student_id}>'


class MasteryState(db.Model):
    """ML-based mastery state per (student, skill) pair"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    
    p_mastery = db.Column(db.Float, nullable=False, default=0.5)
    confidence = db.Column(db.Float, nullable=True, default=0.5)
    attempt_count = db.Column(db.Integer, default=0)
    rolling_accuracy = db.Column(db.Float, nullable=True)
    trend = db.Column(db.Float, nullable=True)
    
    model_version = db.Column(db.String(50), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'skill', name='uq_student_skill'),
    )
    
    user = db.relationship('User', backref='mastery_states')
    
    def __repr__(self):
        return f'<MasteryState Student {self.student_id} Skill {self.skill}: {self.p_mastery:.2f}>'


class RiskScore(db.Model):
    """ML-based at-risk prediction per (student, class) pair"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    
    p_risk = db.Column(db.Float, nullable=False, default=0.5)
    risk_level = db.Column(db.String(20), nullable=True)
    top_drivers_json = db.Column(db.Text, nullable=True)
    
    model_version = db.Column(db.String(50), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='uq_student_class_risk'),
    )
    
    user = db.relationship('User', backref='risk_scores')
    class_obj = db.relationship('Class', backref='risk_scores')
    
    def __repr__(self):
        return f'<RiskScore Student {self.student_id} Class {self.class_id}: {self.p_risk:.2f}>'


class BanditPolicyState(db.Model):
    """Contextual bandit policy state per (student, class) pair"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    
    policy_state_json = db.Column(db.Text, nullable=True)
    bandit_type = db.Column(db.String(50), default='linucb')
    model_version = db.Column(db.String(50), nullable=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='uq_student_class_bandit'),
    )
    
    user = db.relationship('User', backref='bandit_policies')
    class_obj = db.relationship('Class', backref='bandit_policies')
    
    def __repr__(self):
        return f'<BanditPolicyState Student {self.student_id} Class {self.class_id}>'


class ContentEmbedding(db.Model):
    """Embeddings for content retrieval (RAG)"""
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    content_file_id = db.Column(db.Integer, db.ForeignKey('content_file.id'), nullable=True)
    
    chunk_text = db.Column(db.Text, nullable=False)
    embedding_json = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class_obj = db.relationship('Class', backref='content_embeddings')
    content_file = db.relationship('ContentFile', backref='embeddings')
    
    def __repr__(self):
        return f'<ContentEmbedding Class {self.class_id} File {self.content_file_id}>'


class ModelVersion(db.Model):
    """Track ML model versions and metrics"""
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(100), nullable=False)
    
    metrics_json = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('model_type', 'version', name='uq_model_type_version'),
    )
    
    def __repr__(self):
        return f'<ModelVersion {self.model_type} {self.version}>'
    
    def get_val_accuracy(self):
        """Get validation accuracy from metrics_json"""
        if not self.metrics_json:
            return 'N/A'
        try:
            import json
            metrics = json.loads(self.metrics_json)
            val_acc = metrics.get('val_accuracy')
            if val_acc is not None:
                return f"{val_acc:.3f}"
            return 'N/A'
        except:
            return 'N/A'
