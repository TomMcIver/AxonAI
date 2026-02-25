from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import (
    User, Class, Assignment, AssignmentSubmission, Grade, ContentFile,
    ChatMessage
)
from auth import login_required, get_current_user
import json
from datetime import datetime, timedelta

# ============================================================
# MOCK DATA FOR DEMO
# ============================================================

MOCK_TEACHER_CLASSES = [
    {'id': 1, 'name': 'Algebra I', 'subject': 'Math', 'student_count': 25, 'pass_rate': 76},
    {'id': 2, 'name': 'Biology 101', 'subject': 'Science', 'student_count': 22, 'pass_rate': 82},
    {'id': 3, 'name': 'Financial Accounting', 'subject': 'Accounting', 'student_count': 18, 'pass_rate': 68},
]

MOCK_MATERIALS = {
    1: [
        {'name': 'Chapter 5 - Linear Equations', 'type': 'PDF', 'date': 'Feb 10, 2026', 'description': 'Core concepts of linear equations and graphing'},
        {'name': 'Quadratic Functions Slides', 'type': 'Slides', 'date': 'Feb 5, 2026', 'description': 'Introduction to quadratic functions'},
        {'name': 'Practice Problems Set 3', 'type': 'PDF', 'date': 'Jan 28, 2026', 'description': 'Practice problems covering polynomials'},
    ],
    2: [
        {'name': 'Cell Biology Notes', 'type': 'PDF', 'date': 'Feb 12, 2026', 'description': 'Cell structure and organelles'},
        {'name': 'Genetics Overview', 'type': 'Slides', 'date': 'Feb 8, 2026', 'description': 'Introduction to Mendelian genetics'},
    ],
    3: [
        {'name': 'Balance Sheet Fundamentals', 'type': 'PDF', 'date': 'Feb 11, 2026', 'description': 'Understanding balance sheets'},
        {'name': 'Journal Entries Guide', 'type': 'PDF', 'date': 'Feb 3, 2026', 'description': 'How to record journal entries'},
    ],
}

MOCK_ASSIGNMENTS = {
    1: [
        {'title': 'Linear Equations Quiz', 'due_date': 'Mar 1, 2026', 'completed': 18, 'pct': 72},
        {'title': 'Graphing Homework #4', 'due_date': 'Feb 25, 2026', 'completed': 22, 'pct': 88},
        {'title': 'Polynomial Test', 'due_date': 'Feb 15, 2026', 'completed': 25, 'pct': 100},
    ],
    2: [
        {'title': 'Cell Diagram Labeling', 'due_date': 'Mar 3, 2026', 'completed': 15, 'pct': 68},
        {'title': 'Genetics Problem Set', 'due_date': 'Feb 20, 2026', 'completed': 20, 'pct': 91},
    ],
    3: [
        {'title': 'Balance Sheet Exercise', 'due_date': 'Mar 5, 2026', 'completed': 10, 'pct': 56},
        {'title': 'Journal Entries Practice', 'due_date': 'Feb 22, 2026', 'completed': 16, 'pct': 89},
    ],
}

MOCK_METRICS = {
    1: {'trending_up': 7, 'top_performers': 5, 'needs_support': 3},
    2: {'trending_up': 9, 'top_performers': 6, 'needs_support': 2},
    3: {'trending_up': 4, 'top_performers': 3, 'needs_support': 5},
}

MOCK_ANALYTICS = {
    1: {'attendance': 91},
    2: {'attendance': 94},
    3: {'attendance': 87},
}

MOCK_GROUPS = {
    1: [
        {'id': 'a', 'name': 'Group A: Visual Learners', 'description': 'Need mini-lesson on Fractions using visual learning style', 'badge_color': 'orange', 'student_count': 8,
         'summary': '8 students in this group need a mini-lesson on Fractions using visual learning style with focus on number line representation'},
        {'id': 'b', 'name': 'Group B: Problem Solvers', 'description': 'Stuck on Problem-Solving, struggling with engagement', 'badge_color': 'red', 'student_count': 5,
         'summary': '5 students in this group are stuck on Problem-Solving strategies and need hands-on practice with focus on word problems'},
        {'id': 'c', 'name': 'Group C: Advanced Track', 'description': 'Ready for advanced material, excelling in core concepts', 'badge_color': 'green', 'student_count': 12,
         'summary': '12 students in this group are ready for advanced algebraic concepts and would benefit from enrichment activities'},
    ],
    2: [
        {'id': 'a', 'name': 'Group A: Lab Learners', 'description': 'Need hands-on lab work for cell biology concepts', 'badge_color': 'blue', 'student_count': 10,
         'summary': '10 students need hands-on lab activities to reinforce cell biology concepts using microscope work'},
        {'id': 'b', 'name': 'Group B: Concept Builders', 'description': 'Struggling with genetics terminology', 'badge_color': 'orange', 'student_count': 12,
         'summary': '12 students need additional support with genetics vocabulary and Punnett square applications'},
    ],
    3: [
        {'id': 'a', 'name': 'Group A: Practical Accountants', 'description': 'Need more real-world examples for journal entries', 'badge_color': 'orange', 'student_count': 8,
         'summary': '8 students need real-world case studies to understand journal entry applications in business contexts'},
        {'id': 'b', 'name': 'Group B: Strong Foundations', 'description': 'Solid understanding, ready for advanced topics', 'badge_color': 'green', 'student_count': 10,
         'summary': '10 students have strong foundational knowledge and are ready to move on to income statements and cash flow'},
    ],
}

MOCK_STUDENTS = {
    1: [
        {'id': 1, 'name': 'Emma Wilson', 'initials': 'EW', 'grade': 85, 'blocker': 'Quadratic equations', 'ai_engagement': 'High', 'material_engagement': 'High',
         'pass_rate': 85, 'projected_grade': 'A-', 'attendance': 95, 'completion_rate': 92, 'overall_progress': 83,
         'learning_style': 'Visual Learner', 'misconceptions': ['Negative exponents', 'Fraction division'], 'strengths': ['Linear equations', 'Graphing'],
         'ai_summary': 'Emma is performing well overall but struggles with negative exponents. She responds best to visual explanations and step-by-step walkthroughs.',
         'next_steps': ['Provide visual aids for exponent rules', 'Assign targeted practice on fraction operations', 'Consider peer tutoring for reinforcement'],
         'mastery': [{'name': 'Linear Equations', 'score': 92}, {'name': 'Graphing', 'score': 88}, {'name': 'Polynomials', 'score': 75}, {'name': 'Quadratics', 'score': 62}],
         'ai_trend': [40, 55, 60, 70, 80, 85, 90, 88, 92, 95], 'material_trend': [50, 60, 65, 70, 75, 80, 82, 85, 88, 90], 'group': 'a'},
        {'id': 2, 'name': 'Liam Chen', 'initials': 'LC', 'grade': 72, 'blocker': 'Word problems', 'ai_engagement': 'Medium', 'material_engagement': 'Low',
         'pass_rate': 72, 'projected_grade': 'B-', 'attendance': 88, 'completion_rate': 78, 'overall_progress': 70,
         'learning_style': 'Kinesthetic Learner', 'misconceptions': ['Setting up equations from words', 'Unit conversions'], 'strengths': ['Arithmetic', 'Basic algebra'],
         'ai_summary': 'Liam struggles with translating word problems into mathematical expressions. He benefits from hands-on activities and real-world examples.',
         'next_steps': ['Use real-world scenarios for word problems', 'Break complex problems into smaller steps', 'Increase AI tutor engagement with interactive problems'],
         'mastery': [{'name': 'Linear Equations', 'score': 78}, {'name': 'Graphing', 'score': 65}, {'name': 'Polynomials', 'score': 70}, {'name': 'Quadratics', 'score': 48}],
         'ai_trend': [30, 35, 40, 45, 50, 48, 52, 55, 50, 53], 'material_trend': [20, 25, 30, 28, 35, 30, 32, 35, 38, 35], 'group': 'b'},
        {'id': 3, 'name': 'Sofia Patel', 'initials': 'SP', 'grade': 91, 'blocker': 'None - excelling', 'ai_engagement': 'High', 'material_engagement': 'High',
         'pass_rate': 91, 'projected_grade': 'A', 'attendance': 98, 'completion_rate': 100, 'overall_progress': 93,
         'learning_style': 'Reading/Writing', 'misconceptions': [], 'strengths': ['All core topics', 'Problem solving', 'Mathematical reasoning'],
         'ai_summary': 'Sofia is a top performer who consistently exceeds expectations. She uses the AI tutor proactively and would benefit from enrichment challenges.',
         'next_steps': ['Provide advanced challenge problems', 'Consider peer tutoring role', 'Introduce pre-algebra II concepts'],
         'mastery': [{'name': 'Linear Equations', 'score': 95}, {'name': 'Graphing', 'score': 93}, {'name': 'Polynomials', 'score': 90}, {'name': 'Quadratics', 'score': 85}],
         'ai_trend': [70, 75, 80, 85, 88, 90, 92, 95, 93, 96], 'material_trend': [80, 82, 85, 88, 90, 92, 94, 95, 96, 98], 'group': 'c'},
        {'id': 4, 'name': 'Noah Kim', 'initials': 'NK', 'grade': 58, 'blocker': 'Algebra concepts', 'ai_engagement': 'Low', 'material_engagement': 'Low',
         'pass_rate': 58, 'projected_grade': 'D+', 'attendance': 80, 'completion_rate': 65, 'overall_progress': 55,
         'learning_style': 'Auditory Learner', 'misconceptions': ['Variable manipulation', 'Order of operations', 'Equation balancing'], 'strengths': ['Basic computation'],
         'ai_summary': 'Noah is at risk and needs immediate support. He rarely engages with the AI tutor or class materials. Consider reaching out to discuss barriers to learning.',
         'next_steps': ['Schedule one-on-one check-in', 'Set up structured AI tutor sessions', 'Contact parent about engagement concerns'],
         'mastery': [{'name': 'Linear Equations', 'score': 55}, {'name': 'Graphing', 'score': 50}, {'name': 'Polynomials', 'score': 45}, {'name': 'Quadratics', 'score': 30}],
         'ai_trend': [20, 22, 18, 25, 20, 15, 18, 20, 22, 20], 'material_trend': [15, 18, 20, 15, 18, 20, 15, 18, 20, 18], 'group': 'b'},
        {'id': 5, 'name': 'Olivia Martinez', 'initials': 'OM', 'grade': 79, 'blocker': 'Graphing inequalities', 'ai_engagement': 'Medium', 'material_engagement': 'High',
         'pass_rate': 79, 'projected_grade': 'B+', 'attendance': 92, 'completion_rate': 88, 'overall_progress': 77,
         'learning_style': 'Visual Learner', 'misconceptions': ['Inequality direction changes', 'Shading regions'], 'strengths': ['Equations', 'Substitution'],
         'ai_summary': 'Olivia shows steady improvement and engages well with materials. She needs targeted support on graphing inequalities, particularly with boundary conditions.',
         'next_steps': ['Provide graphing calculator practice', 'Assign inequality visualization exercises', 'Pair with peer for collaborative graphing work'],
         'mastery': [{'name': 'Linear Equations', 'score': 85}, {'name': 'Graphing', 'score': 68}, {'name': 'Polynomials', 'score': 80}, {'name': 'Quadratics', 'score': 60}],
         'ai_trend': [40, 45, 50, 55, 58, 62, 65, 68, 70, 72], 'material_trend': [60, 65, 70, 72, 75, 78, 80, 82, 85, 88], 'group': 'a'},
    ],
}

# Generate students for other classes
MOCK_STUDENTS[2] = [
    {'id': 6, 'name': 'Ava Thompson', 'initials': 'AT', 'grade': 88, 'blocker': 'Genetics notation', 'ai_engagement': 'High', 'material_engagement': 'High',
     'pass_rate': 88, 'projected_grade': 'A-', 'attendance': 96, 'completion_rate': 95, 'overall_progress': 87,
     'learning_style': 'Visual Learner', 'misconceptions': ['Punnett square ratios'], 'strengths': ['Cell biology', 'Lab work', 'Scientific method'],
     'ai_summary': 'Ava is a strong student who excels in lab-based learning. Minor struggles with genetics notation can be addressed with targeted practice.',
     'next_steps': ['Provide genetics notation cheat sheet', 'Assign Punnett square practice problems'],
     'mastery': [{'name': 'Cell Biology', 'score': 94}, {'name': 'Genetics', 'score': 75}, {'name': 'Ecology', 'score': 88}, {'name': 'Evolution', 'score': 82}],
     'ai_trend': [60, 65, 70, 75, 80, 85, 88, 90, 92, 94], 'material_trend': [70, 75, 78, 80, 82, 85, 88, 90, 92, 95], 'group': 'a'},
    {'id': 7, 'name': 'Ethan Brooks', 'initials': 'EB', 'grade': 74, 'blocker': 'Cell organelle functions', 'ai_engagement': 'Medium', 'material_engagement': 'Medium',
     'pass_rate': 74, 'projected_grade': 'B-', 'attendance': 89, 'completion_rate': 82, 'overall_progress': 72,
     'learning_style': 'Kinesthetic Learner', 'misconceptions': ['Mitochondria vs chloroplast', 'Cell membrane transport'], 'strengths': ['Ecology', 'Observation skills'],
     'ai_summary': 'Ethan learns best through hands-on activities. Needs more lab time to reinforce cell biology concepts.',
     'next_steps': ['Schedule extra lab sessions', 'Use 3D cell models for visualization', 'Create flashcard practice routine'],
     'mastery': [{'name': 'Cell Biology', 'score': 65}, {'name': 'Genetics', 'score': 70}, {'name': 'Ecology', 'score': 85}, {'name': 'Evolution', 'score': 78}],
     'ai_trend': [40, 45, 48, 50, 55, 58, 60, 62, 58, 60], 'material_trend': [50, 52, 55, 58, 60, 62, 60, 58, 62, 65], 'group': 'b'},
]

MOCK_STUDENTS[3] = [
    {'id': 8, 'name': 'Mia Johnson', 'initials': 'MJ', 'grade': 82, 'blocker': 'Depreciation methods', 'ai_engagement': 'High', 'material_engagement': 'Medium',
     'pass_rate': 82, 'projected_grade': 'B+', 'attendance': 93, 'completion_rate': 90, 'overall_progress': 80,
     'learning_style': 'Reading/Writing', 'misconceptions': ['Straight-line vs declining balance'], 'strengths': ['Journal entries', 'Balance sheets'],
     'ai_summary': 'Mia has strong foundational skills but needs support with depreciation concepts. She responds well to textbook-style explanations.',
     'next_steps': ['Provide depreciation comparison worksheet', 'Assign real-world depreciation scenarios'],
     'mastery': [{'name': 'Journal Entries', 'score': 90}, {'name': 'Balance Sheets', 'score': 85}, {'name': 'Income Statements', 'score': 72}, {'name': 'Depreciation', 'score': 58}],
     'ai_trend': [50, 55, 60, 65, 70, 75, 78, 80, 82, 85], 'material_trend': [55, 58, 60, 62, 65, 68, 70, 68, 65, 68], 'group': 'a'},
    {'id': 9, 'name': 'James Lee', 'initials': 'JL', 'grade': 65, 'blocker': 'Debits and credits', 'ai_engagement': 'Low', 'material_engagement': 'Low',
     'pass_rate': 65, 'projected_grade': 'C', 'attendance': 82, 'completion_rate': 70, 'overall_progress': 60,
     'learning_style': 'Auditory Learner', 'misconceptions': ['Debit vs credit rules', 'Account classification'], 'strengths': ['Arithmetic accuracy'],
     'ai_summary': 'James is struggling with fundamental accounting concepts. Needs a back-to-basics intervention focused on the debit/credit framework.',
     'next_steps': ['Provide one-on-one tutoring session', 'Create simplified debit/credit reference guide', 'Increase AI tutor interaction frequency'],
     'mastery': [{'name': 'Journal Entries', 'score': 60}, {'name': 'Balance Sheets', 'score': 55}, {'name': 'Income Statements', 'score': 50}, {'name': 'Depreciation', 'score': 40}],
     'ai_trend': [20, 22, 25, 20, 22, 25, 28, 25, 22, 20], 'material_trend': [15, 18, 20, 22, 20, 18, 20, 22, 20, 18], 'group': 'a'},
]

# Mock student assignments (for student dashboard)
MOCK_STUDENT_ASSIGNMENTS = {
    1: [
        {'title': 'Linear Equations Quiz', 'status': 'In Progress', 'status_class': 'in-progress', 'due_date': 'Mar 1, 2026', 'days_left': 4, 'due_color': 'due-yellow'},
        {'title': 'Graphing Homework #4', 'status': 'Not Started', 'status_class': 'not-started', 'due_date': 'Feb 25, 2026', 'days_left': 0, 'due_color': 'due-red'},
        {'title': 'Polynomial Test', 'status': 'Graded', 'status_class': 'graded', 'due_date': 'Feb 15, 2026', 'days_left': -10, 'due_color': 'due-green'},
    ],
    2: [
        {'title': 'Cell Diagram Labeling', 'status': 'Not Started', 'status_class': 'not-started', 'due_date': 'Mar 3, 2026', 'days_left': 6, 'due_color': 'due-green'},
        {'title': 'Genetics Problem Set', 'status': 'Submitted', 'status_class': 'submitted', 'due_date': 'Feb 20, 2026', 'days_left': -5, 'due_color': 'due-green'},
    ],
    3: [
        {'title': 'Balance Sheet Exercise', 'status': 'In Progress', 'status_class': 'in-progress', 'due_date': 'Mar 5, 2026', 'days_left': 8, 'due_color': 'due-green'},
        {'title': 'Journal Entries Practice', 'status': 'Graded', 'status_class': 'graded', 'due_date': 'Feb 22, 2026', 'days_left': -3, 'due_color': 'due-green'},
    ],
}

MOCK_CHAT_SESSIONS = {
    1: [
        {'date': 'Feb 24, 2026', 'duration': '15 min', 'summary': 'Mastered: Solving two-step equations', 'notes': "You've made great progress with equation solving techniques."},
        {'date': 'Feb 20, 2026', 'duration': '22 min', 'summary': 'Worked on: Graphing linear functions', 'notes': "You've overcome the confusion with slope-intercept form."},
        {'date': 'Feb 18, 2026', 'duration': '10 min', 'summary': 'Reviewed: Polynomial basics', 'notes': 'Good understanding of terms and coefficients.'},
    ],
    2: [
        {'date': 'Feb 23, 2026', 'duration': '18 min', 'summary': 'Studied: Cell membrane transport', 'notes': "You've moved forward in understanding osmosis and diffusion."},
    ],
    3: [],
}

# Mock parent data
MOCK_CHILDREN = [
    {
        'id': 1, 'name': 'Emma Wilson', 'initials': 'EW', 'classes_count': 3, 'trend': 'up', 'trend_label': 'Improving',
        'year_level': 'Year 11', 'ai_interactions': 12, 'completion_rate': 92, 'avg_study_time': '1.5 hrs',
        'classes': [
            {'name': 'Algebra I', 'subject': 'Math', 'grade': 85, 'trend': 'up',
             'going_well': ['Linear equations', 'Graphing'], 'needs_help': ['Quadratic equations']},
            {'name': 'Biology 101', 'subject': 'Science', 'grade': 78, 'trend': 'stable',
             'going_well': ['Cell biology'], 'needs_help': ['Genetics notation']},
            {'name': 'Financial Accounting', 'subject': 'Accounting', 'grade': 82, 'trend': 'up',
             'going_well': ['Journal entries', 'Balance sheets'], 'needs_help': ['Depreciation']},
        ],
        'blockers': [
            {'subject': 'Math', 'issue': 'Struggling with quadratic equations, particularly factoring'},
            {'subject': 'Science', 'issue': 'Needs help with Punnett square notation and ratios'},
        ],
        'recommendations': [
            'Emma would benefit from visual aids when learning quadratic equations - consider graphing calculator exercises.',
            'Her biology performance could improve with additional genetics practice worksheets.',
            'Overall trajectory is positive - maintain current study habits and AI tutor engagement.',
        ],
    },
]


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Home page with login buttons"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login - mock auth with role buttons"""
    if request.method == 'GET':
        return redirect(url_for('index'))

    user_type = request.form.get('user_type')

    if not user_type:
        flash('Please select a role.', 'danger')
        return redirect(url_for('index'))

    if user_type == 'parent':
        # Mock parent login - no DB user needed
        session['user_id'] = -1  # sentinel value for parent
        session['user_role'] = 'parent'
        session['user_name'] = 'Sarah Wilson'
        flash('Welcome, Sarah!', 'success')
        return redirect(url_for('dashboard'))

    if user_type == 'teacher':
        # Find first teacher or create mock session
        try:
            user = User.query.filter_by(role='teacher', is_active=True).first()
            if user:
                session['user_id'] = user.id
                session['user_role'] = 'teacher'
                session['user_name'] = user.get_full_name()
                flash(f'Welcome, {user.get_full_name()}!', 'success')
                return redirect(url_for('dashboard'))
        except Exception:
            pass
        # Mock teacher session
        session['user_id'] = -2
        session['user_role'] = 'teacher'
        session['user_name'] = 'Mr. Anderson'
        flash('Welcome, Mr. Anderson!', 'success')
        return redirect(url_for('dashboard'))

    if user_type == 'student':
        # Student login uses real DB
        try:
            user = User.query.filter_by(role='student', is_active=True).first()
            if user:
                session['user_id'] = user.id
                session['user_role'] = 'student'
                session['user_name'] = user.get_full_name()
                flash(f'Welcome, {user.get_full_name()}!', 'success')
                return redirect(url_for('dashboard'))
        except Exception:
            pass
        # Fallback mock student
        session['user_id'] = -3
        session['user_role'] = 'student'
        session['user_name'] = 'Emma Wilson'
        flash('Welcome, Emma!', 'success')
        return redirect(url_for('dashboard'))

    flash('Invalid role selected.', 'danger')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Clear session and redirect to home"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Route to role-specific dashboard"""
    role = session.get('user_role')
    if role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'parent':
        return redirect(url_for('parent_dashboard'))
    else:
        flash('Unknown role.', 'danger')
        return redirect(url_for('index'))


# ============================================================
# TEACHER ROUTES
# ============================================================

@app.route('/teacher')
@app.route('/teacher/classes')
@login_required
def teacher_dashboard():
    """Teacher class selection view"""
    # Try to load real classes from DB for this teacher
    user_id = session.get('user_id')
    if user_id and user_id > 0:
        try:
            db_classes = Class.query.filter_by(teacher_id=user_id, is_active=True).all()
            if db_classes:
                classes = []
                for c in db_classes:
                    classes.append({
                        'id': c.id,
                        'name': c.name,
                        'subject': c.subject or 'General',
                        'student_count': c.get_student_count(),
                        'pass_rate': round(c.get_pass_rate()),
                    })
                return render_template('teacher_classes.html', classes=classes)
        except Exception:
            pass

    # Fallback to mock data
    return render_template('teacher_classes.html', classes=MOCK_TEACHER_CLASSES)


@app.route('/teacher/class/<int:class_id>')
@login_required
def teacher_class_dashboard(class_id):
    """Teacher class dashboard with sidebar"""
    # Try real DB first
    db_class = None
    try:
        db_class = Class.query.get(class_id)
    except Exception:
        pass
    if db_class:
        try:
            cls = {
                'id': db_class.id,
                'name': db_class.name,
                'subject': db_class.subject or 'General',
                'student_count': db_class.get_student_count(),
                'pass_rate': round(db_class.get_pass_rate()),
            }
            materials = []
            for cf in db_class.content_files:
                materials.append({
                    'name': cf.name,
                    'type': cf.file_type.upper() if cf.file_type else 'File',
                    'date': cf.uploaded_at.strftime('%b %d, %Y') if cf.uploaded_at else '',
                    'description': cf.name,
                })
            assignments = []
            for a in db_class.assignments:
                sub_count = len(a.submissions)
                total = db_class.get_student_count() or 1
                pct = round((sub_count / total) * 100)
                assignments.append({
                    'title': a.title,
                    'due_date': a.due_date.strftime('%b %d, %Y') if a.due_date else 'No due date',
                    'completed': sub_count,
                    'pct': pct,
                })
            students_list = []
            for s in db_class.get_students():
                avg = s.get_class_average(class_id)
                chat_info = s.get_chat_summary(class_id)
                students_list.append({
                    'id': s.id,
                    'name': s.get_full_name(),
                    'initials': s.first_name[0] + s.last_name[0] if s.last_name else s.first_name[0],
                    'grade': round(avg) if avg else 0,
                    'blocker': 'No data available',
                    'ai_engagement': chat_info.get('engagement_level', 'Low').capitalize(),
                    'material_engagement': 'Medium',
                })
            metrics = MOCK_METRICS.get(class_id, MOCK_METRICS[1])
            analytics = MOCK_ANALYTICS.get(class_id, MOCK_ANALYTICS[1])
            groups = MOCK_GROUPS.get(class_id, MOCK_GROUPS[1])
            if not materials:
                materials = MOCK_MATERIALS.get(class_id, MOCK_MATERIALS[1])
            if not assignments:
                assignments = MOCK_ASSIGNMENTS.get(class_id, MOCK_ASSIGNMENTS[1])
            if not students_list:
                students_list = MOCK_STUDENTS.get(class_id, MOCK_STUDENTS[1])
            return render_template('teacher_class_dashboard.html',
                cls=cls, materials=materials, assignments=assignments,
                metrics=metrics, analytics=analytics, groups=groups,
                students=students_list)
        except Exception:
            pass

    # Full mock fallback
    cls_data = next((c for c in MOCK_TEACHER_CLASSES if c['id'] == class_id), MOCK_TEACHER_CLASSES[0])
    return render_template('teacher_class_dashboard.html',
        cls=cls_data,
        materials=MOCK_MATERIALS.get(class_id, MOCK_MATERIALS[1]),
        assignments=MOCK_ASSIGNMENTS.get(class_id, MOCK_ASSIGNMENTS[1]),
        metrics=MOCK_METRICS.get(class_id, MOCK_METRICS[1]),
        analytics=MOCK_ANALYTICS.get(class_id, MOCK_ANALYTICS[1]),
        groups=MOCK_GROUPS.get(class_id, MOCK_GROUPS[1]),
        students=MOCK_STUDENTS.get(class_id, MOCK_STUDENTS[1]))


@app.route('/teacher/class/<int:class_id>/group/<group_id>')
@login_required
def teacher_group(class_id, group_id):
    """Teacher group view - students in a specific group"""
    cls_data = next((c for c in MOCK_TEACHER_CLASSES if c['id'] == class_id), MOCK_TEACHER_CLASSES[0])
    groups = MOCK_GROUPS.get(class_id, MOCK_GROUPS[1])
    group = next((g for g in groups if g['id'] == group_id), groups[0])

    all_students = MOCK_STUDENTS.get(class_id, MOCK_STUDENTS[1])
    group_students = [s for s in all_students if s.get('group') == group_id]
    if not group_students:
        group_students = all_students[:3]

    return render_template('teacher_group.html',
        class_id=class_id,
        class_name=cls_data['name'],
        group=group,
        students=group_students)


@app.route('/teacher/class/<int:class_id>/student/<int:student_id>')
@login_required
def teacher_student(class_id, student_id):
    """Individual student view with full metrics"""
    cls_data = next((c for c in MOCK_TEACHER_CLASSES if c['id'] == class_id), MOCK_TEACHER_CLASSES[0])

    # Try DB first
    try:
        db_student = User.query.get(student_id)
        if db_student and db_student.role == 'student':
            avg = db_student.get_class_average(class_id) or 0
            chat_info = db_student.get_chat_summary(class_id)

            all_mock = MOCK_STUDENTS.get(class_id, MOCK_STUDENTS[1])
            mock_match = next((s for s in all_mock if s['id'] == student_id), None)

            if mock_match:
                student = mock_match
            else:
                student = {
                    'id': db_student.id,
                    'name': db_student.get_full_name(),
                    'initials': db_student.first_name[0] + (db_student.last_name[0] if db_student.last_name else ''),
                    'grade': round(avg),
                    'pass_rate': round(avg),
                    'projected_grade': 'B' if avg >= 70 else 'C' if avg >= 60 else 'D',
                    'attendance': round(db_student.attendance_rate or 85),
                    'completion_rate': 80,
                    'overall_progress': round(avg),
                    'learning_style': db_student.learning_style or 'Not assessed',
                    'misconceptions': [],
                    'strengths': [],
                    'ai_summary': f'{db_student.get_full_name()} is currently at {round(avg)}% in this class.',
                    'next_steps': ['Continue current study habits', 'Engage more with AI tutor'],
                    'mastery': [{'name': 'General', 'score': round(avg)}],
                    'ai_engagement': chat_info.get('engagement_level', 'Low').capitalize(),
                    'material_engagement': 'Medium',
                    'ai_trend': [50, 55, 60, 58, 62, 65, 68, 70, 72, 75],
                    'material_trend': [40, 45, 50, 55, 58, 60, 62, 65, 68, 70],
                }

            return render_template('teacher_student.html',
                student=student, class_id=class_id, class_name=cls_data['name'])
    except Exception:
        pass

    # Full mock fallback
    all_students = MOCK_STUDENTS.get(class_id, MOCK_STUDENTS[1])
    student = next((s for s in all_students if s['id'] == student_id), all_students[0])

    return render_template('teacher_student.html',
        student=student, class_id=class_id, class_name=cls_data['name'])


# ============================================================
# STUDENT ROUTES
# ============================================================

@app.route('/student')
@app.route('/student/classes')
@login_required
def student_dashboard():
    """Student class selection view"""
    user_id = session.get('user_id')

    # Try real DB for student data
    if user_id and user_id > 0:
        try:
            user = User.query.get(user_id)
            if user and user.role == 'student' and user.classes:
                classes = []
                for c in user.classes:
                    grade = user.get_class_average(c.id)
                    teacher = User.query.get(c.teacher_id)
                    classes.append({
                        'id': c.id,
                        'name': c.name,
                        'subject': c.subject or 'General',
                        'teacher_name': teacher.get_full_name() if teacher else 'Unknown',
                        'grade': round(grade) if grade is not None else None,
                    })
                return render_template('student_classes.html', classes=classes)
        except Exception:
            pass

    # Mock student classes
    mock_classes = [
        {'id': 1, 'name': 'Algebra I', 'subject': 'Math', 'teacher_name': 'Mr. Anderson', 'grade': 85},
        {'id': 2, 'name': 'Biology 101', 'subject': 'Science', 'teacher_name': 'Ms. Rivera', 'grade': 78},
        {'id': 3, 'name': 'Financial Accounting', 'subject': 'Accounting', 'teacher_name': 'Dr. Chen', 'grade': 82},
    ]
    return render_template('student_classes.html', classes=mock_classes)


@app.route('/student/class/<int:class_id>')
@login_required
def student_class_view(class_id):
    """Student class view with tabs: assignments, materials, AI chat summary"""
    user_id = session.get('user_id')

    # Try real DB
    if user_id and user_id > 0:
        try:
            user = User.query.get(user_id)
            db_class = Class.query.get(class_id)

            if user and db_class and user in db_class.users:
                teacher = User.query.get(db_class.teacher_id)
                cls = {
                    'id': db_class.id,
                    'name': db_class.name,
                    'subject': db_class.subject or 'General',
                    'teacher_name': teacher.get_full_name() if teacher else 'Unknown',
                }

                assignments = []
                for a in db_class.assignments:
                    sub = a.get_submission_by_student(user_id)
                    grade = Grade.query.filter_by(assignment_id=a.id, student_id=user_id).first()
                    if grade:
                        status, status_class = 'Graded', 'graded'
                    elif sub:
                        status, status_class = 'Submitted', 'submitted'
                    else:
                        status, status_class = 'Not Started', 'not-started'

                    days_left = (a.due_date - datetime.utcnow()).days if a.due_date else 0
                    if days_left > 3:
                        due_color = 'due-green'
                    elif days_left > 0:
                        due_color = 'due-yellow'
                    else:
                        due_color = 'due-red'

                    assignments.append({
                        'title': a.title,
                        'status': status,
                        'status_class': status_class,
                        'due_date': a.due_date.strftime('%b %d, %Y') if a.due_date else 'No due date',
                        'days_left': days_left,
                        'due_color': due_color,
                    })

                materials = []
                for cf in db_class.content_files:
                    materials.append({
                        'name': cf.name,
                        'type': cf.file_type.upper() if cf.file_type else 'File',
                        'description': cf.name,
                    })

                chat_sessions = []
                chats = ChatMessage.query.filter_by(
                    user_id=user_id, class_id=class_id
                ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                for chat in chats:
                    chat_sessions.append({
                        'date': chat.created_at.strftime('%b %d, %Y') if chat.created_at else '',
                        'duration': '~10 min',
                        'summary': chat.message[:60] + '...' if len(chat.message) > 60 else chat.message,
                        'notes': chat.response[:80] + '...' if len(chat.response) > 80 else chat.response,
                    })

                if not assignments:
                    assignments = MOCK_STUDENT_ASSIGNMENTS.get(class_id, [])
                if not materials:
                    materials = MOCK_MATERIALS.get(class_id, [])
                if not chat_sessions:
                    chat_sessions = MOCK_CHAT_SESSIONS.get(class_id, [])

                return render_template('student_class_view.html',
                    cls=cls, assignments=assignments, materials=materials,
                    chat_sessions=chat_sessions)
        except Exception:
            pass

    # Mock fallback
    mock_cls_names = {1: ('Algebra I', 'Math', 'Mr. Anderson'), 2: ('Biology 101', 'Science', 'Ms. Rivera'), 3: ('Financial Accounting', 'Accounting', 'Dr. Chen')}
    name, subject, teacher = mock_cls_names.get(class_id, ('Class', 'General', 'Teacher'))
    cls = {'id': class_id, 'name': name, 'subject': subject, 'teacher_name': teacher}

    return render_template('student_class_view.html',
        cls=cls,
        assignments=MOCK_STUDENT_ASSIGNMENTS.get(class_id, []),
        materials=MOCK_MATERIALS.get(class_id, []),
        chat_sessions=MOCK_CHAT_SESSIONS.get(class_id, []))


@app.route('/student/class/<int:class_id>/chat')
@login_required
def student_chat(class_id):
    """AI Chat interface"""
    user_id = session.get('user_id')
    student_name = session.get('user_name', 'Student')
    initials = ''.join([w[0] for w in student_name.split()[:2]]) if student_name else 'S'

    mock_cls_names = {1: ('Algebra I', 'Math'), 2: ('Biology 101', 'Science'), 3: ('Financial Accounting', 'Accounting')}
    class_name, subject = mock_cls_names.get(class_id, ('Class', 'General'))

    # Try to get class name from DB
    try:
        db_class = Class.query.get(class_id)
        if db_class:
            class_name = db_class.name
            subject = db_class.subject or 'General'
    except Exception:
        pass

    # Load chat history from DB
    messages = []
    if user_id and user_id > 0:
        try:
            chats = ChatMessage.query.filter_by(
                user_id=user_id, class_id=class_id
            ).order_by(ChatMessage.created_at.asc()).all()
            for chat in chats:
                messages.append({'role': 'user', 'content': chat.message})
                messages.append({'role': 'ai', 'content': chat.response})
        except Exception:
            pass

    return render_template('student_chat.html',
        class_id=class_id,
        class_name=class_name,
        subject=subject,
        student_initials=initials,
        messages=messages)


# ============================================================
# PARENT ROUTES
# ============================================================

@app.route('/parent')
@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    """Parent child selection view"""
    return render_template('parent_dashboard.html', children=MOCK_CHILDREN)


@app.route('/parent/child/<int:child_id>')
@login_required
def parent_child_view(child_id):
    """Parent child profile view"""
    child = next((c for c in MOCK_CHILDREN if c['id'] == child_id), MOCK_CHILDREN[0])
    return render_template('parent_child.html', child=child)
