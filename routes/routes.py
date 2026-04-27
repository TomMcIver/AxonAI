from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models.models import (
    User, Class, Assignment, AssignmentSubmission, Grade, ContentFile,
    ChatMessage
)
from utils.auth import login_required, get_current_user
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
            groups = []
            if not materials:
                materials = MOCK_MATERIALS.get(class_id, MOCK_MATERIALS[1])
            if not assignments:
                assignments = MOCK_ASSIGNMENTS.get(class_id, MOCK_ASSIGNMENTS[1])
            return render_template('teacher_class_dashboard.html',
                cls=cls, materials=materials, assignments=assignments,
                metrics=metrics, analytics=analytics, groups=groups,
                students=students_list)
        except Exception:
            pass

    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501


@app.route('/teacher/class/<int:class_id>/group/<group_id>')
@login_required
def teacher_group(class_id, group_id):
    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501


@app.route('/teacher/class/<int:class_id>/student/<int:student_id>')
@login_required
def teacher_student(class_id, student_id):
    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501


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

                return render_template('student_class_view.html',
                    cls=cls, assignments=assignments, materials=materials,
                    chat_sessions=chat_sessions)
        except Exception:
            pass

    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501


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
    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501


@app.route('/parent/child/<int:child_id>')
@login_required
def parent_child_view(child_id):
    return jsonify({"error": "not implemented", "detail": "this endpoint is not yet live"}), 501
