from app import db
from datetime import datetime

# Association table for many-to-many relationship between users and classes
class_users = db.Table('class_users',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    photo_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    classes = db.relationship('Class', secondary=class_users, back_populates='users')
    submitted_assignments = db.relationship('AssignmentSubmission', back_populates='student')
    grades = db.relationship('Grade', foreign_keys='Grade.student_id', back_populates='student')

    def __repr__(self):
        return f'<User {self.email}>'

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

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    users = db.relationship('User', secondary=class_users, back_populates='classes')
    assignments = db.relationship('Assignment', back_populates='class_obj')
    content_files = db.relationship('ContentFile', back_populates='class_obj')

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
