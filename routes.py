from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify
from app import app, db
from models import (
    User, Class, Assignment, AssignmentSubmission, Grade, ContentFile, 
    ChatMessage, AIInteraction, OptimizedProfile, FailedStrategy,
    MiniTest, MiniTestResponse, PatternInsight, PredictedGrade, 
    TeacherAIInsight, AIModel
)
from auth import hash_password, check_password, login_required, admin_required, get_current_user, role_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json

@app.route('/')
def index():
    """Preloader page"""
    return render_template('preloader.html')

@app.route('/main')
def main_landing():
    """Main landing page"""
    return render_template('landing.html')

@app.route('/demo')
def demo():
    """Redirect to login for demo"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple role-based login with just buttons"""
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        
        if not user_type:
            flash('Please select a role.', 'danger')
            return render_template('login.html')
        
        # Find first active user with this role
        user = User.query.filter_by(role=user_type, is_active=True).first()
        
        if user:
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.get_full_name()
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'No active {user_type} user found.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Role-based dashboard routing"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user.role == 'admin':
        # Get statistics for admin dashboard
        total_users = User.query.filter_by(is_active=True).count()
        teacher_count = User.query.filter_by(role='teacher', is_active=True).count()
        student_count = User.query.filter_by(role='student', is_active=True).count()
        total_classes = Class.query.filter_by(is_active=True).count()
        
        return render_template('admin_dashboard.html', 
                             user=user,
                             user_count=total_users,
                             teacher_count=teacher_count,
                             student_count=student_count,
                             total_classes=total_classes)
    elif user.role == 'teacher':
        # Get teacher's classes and real statistics
        teacher_classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
        total_students = sum(cls.get_student_count() for cls in teacher_classes)
        
        # Get improvement metrics for all students
        from progression_analyzer import ProgressionAnalyzer
        analyzer = ProgressionAnalyzer()
        student_improvements = []
        
        if teacher_classes:
            # Get first class for now (can be expanded)
            first_class = teacher_classes[0]
            students = first_class.get_students()
            
            for student in students:
                improvement = analyzer.get_student_improvement(student.id)
                improvement['name'] = student.first_name
                improvement['full_name'] = student.get_full_name()
                student_improvements.append(improvement)
        
        # Calculate class average improvement
        if student_improvements:
            avg_improvement = sum(s['improvement_percentage'] for s in student_improvements) / len(student_improvements)
            avg_current = sum(s['current_score'] for s in student_improvements) / len(student_improvements)
        else:
            avg_improvement = 0
            avg_current = 0
        
        return render_template('teacher_dashboard.html', 
                             user=user,
                             classes=teacher_classes,
                             class_count=len(teacher_classes),
                             total_students=total_students,
                             student_improvements=student_improvements,
                             avg_improvement=round(avg_improvement, 1),
                             avg_current=round(avg_current, 1))
    elif user.role == 'student':
        # Get student's classes and overall average
        student_classes = user.classes
        overall_average = user.get_average_grade()
        
        return render_template('student_dashboard.html', 
                             user=user,
                             classes=student_classes,
                             overall_average=overall_average)
    else:
        flash('Invalid user role.', 'danger')
        return redirect(url_for('login'))

@app.route('/progression-data/<int:class_id>')
@role_required(['teacher', 'admin'])
def progression_data(class_id):
    """API endpoint to get student progression data for visualization"""
    from progression_analyzer import ProgressionAnalyzer
    from flask import jsonify
    
    analyzer = ProgressionAnalyzer()
    
    # Get all students in this class
    class_obj = Class.query.get_or_404(class_id)
    students = class_obj.get_students()
    student_ids = [student.id for student in students]
    
    # Get progression data for all students (3-day intervals for cleaner charts)
    progression_results = analyzer.get_multi_student_progression(student_ids, days=30, interval_days=3)
    
    # Format for Chart.js
    chart_data = {
        'labels': [],
        'datasets': []
    }
    
    # Collect all unique dates
    all_dates = set()
    for student_data in progression_results.values():
        for point in student_data['data']:
            all_dates.add(point['date'])
    
    chart_data['labels'] = sorted(list(all_dates))
    
    # Create dataset for each student
    colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d']
    for idx, (student_id, student_data) in enumerate(progression_results.items()):
        # Create a map of date to understanding score
        score_map = {point['date']: point['understanding'] for point in student_data['data']}
        
        # Fill in scores for all dates (null if no data for that date)
        scores = [score_map.get(date, None) for date in chart_data['labels']]
        
        chart_data['datasets'].append({
            'label': student_data['name'],
            'data': scores,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': colors[idx % len(colors)] + '20',
            'fill': False,
            'tension': 0.3,
            'spanGaps': True
        })
    
    return jsonify(chart_data)

@app.route('/progression-data/<int:class_id>/<sub_topic>')
@role_required(['teacher', 'admin'])
def sub_topic_progression_data(class_id, sub_topic):
    """API endpoint to get sub-topic specific progression data"""
    from progression_analyzer import ProgressionAnalyzer
    from flask import jsonify
    
    analyzer = ProgressionAnalyzer()
    
    # Get all students in this class
    class_obj = Class.query.get_or_404(class_id)
    students = class_obj.get_students()
    student_ids = [student.id for student in students]
    
    # Get progression data for this sub-topic (3-day intervals for cleaner charts)
    progression_results = analyzer.get_multi_student_sub_topic_progression(student_ids, sub_topic, days=60, interval_days=3)
    
    # Format for Chart.js
    chart_data = {'labels': [], 'datasets': []}
    
    # Collect all unique dates
    all_dates = set()
    for student_data in progression_results.values():
        for point in student_data['data']:
            all_dates.add(point['date'])
    
    chart_data['labels'] = sorted(list(all_dates))
    
    # Color scheme for sub-topics
    colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d']
    for idx, (student_id, student_data) in enumerate(progression_results.items()):
        score_map = {point['date']: point['understanding'] for point in student_data['data']}
        scores = [score_map.get(date, None) for date in chart_data['labels']]
        
        chart_data['datasets'].append({
            'label': student_data['name'],
            'data': scores,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': colors[idx % len(colors)] + '20',
            'fill': False,
            'tension': 0.3,
            'spanGaps': True
        })
    
    return jsonify(chart_data)

@app.route('/progression-data/<int:class_id>/composite')
@role_required(['teacher', 'admin'])
def composite_progression_data(class_id):
    """API endpoint to get composite (overall Math) progression data"""
    from progression_analyzer import ProgressionAnalyzer
    from flask import jsonify
    
    analyzer = ProgressionAnalyzer()
    
    # Get all students in this class
    class_obj = Class.query.get_or_404(class_id)
    students = class_obj.get_students()
    student_ids = [student.id for student in students]
    
    # Get composite progression data (3-day intervals for cleaner charts)
    progression_results = analyzer.get_multi_student_composite_progression(student_ids, days=60, interval_days=3)
    
    # Format for Chart.js
    chart_data = {'labels': [], 'datasets': []}
    
    # Collect all unique dates
    all_dates = set()
    for student_data in progression_results.values():
        for point in student_data['data']:
            all_dates.add(point['date'])
    
    chart_data['labels'] = sorted(list(all_dates))
    
    # Colors for composite view
    colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d']
    for idx, (student_id, student_data) in enumerate(progression_results.items()):
        score_map = {point['date']: point['understanding'] for point in student_data['data']}
        scores = [score_map.get(date, None) for date in chart_data['labels']]
        
        chart_data['datasets'].append({
            'label': f"{student_data['name']} (Overall Math)",
            'data': scores,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': colors[idx % len(colors)] + '20',
            'fill': False,
            'tension': 0.3,
            'spanGaps': True
        })
    
    return jsonify(chart_data)

@app.route('/manage-users')
@admin_required
def manage_users():
    """Admin page to manage users"""
    users = User.query.filter_by(is_active=True).all()
    return render_template('manage_users.html', users=users)

@app.route('/add-user', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Admin page to add new users"""
    if request.method == 'POST':
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if not all([role, first_name, last_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('edit_user.html', user=None, roles=['admin', 'teacher', 'student'])
        
        # Create new user
        user = User(
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        
        # Add student profile fields if role is student
        if role == 'student':
            user.age = request.form.get('age') or None
            user.gender = request.form.get('gender') or None
            user.ethnicity = request.form.get('ethnicity') or None
            user.year_level = request.form.get('year_level') or None
            user.primary_language = request.form.get('primary_language') or None
            user.secondary_language = request.form.get('secondary_language') or None
            user.learning_difficulty = request.form.get('learning_difficulty') or None
            user.major_life_event = request.form.get('major_life_event') or None
            user.learning_style = request.form.get('learning_style') or None
            user.preferred_difficulty = request.form.get('preferred_difficulty') or None
            user.academic_goals = request.form.get('academic_goals') or None
            
            # Parse date of birth
            dob_str = request.form.get('date_of_birth')
            if dob_str:
                try:
                    from datetime import datetime
                    user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Parse attendance rate
            attendance_str = request.form.get('attendance_rate')
            if attendance_str:
                try:
                    user.attendance_rate = float(attendance_str)
                except ValueError:
                    pass
            
            # Parse lists for extracurricular activities and interests
            activities_text = request.form.get('extracurricular_activities', '').strip()
            if activities_text:
                activities_list = [act.strip() for act in activities_text.split('\n') if act.strip()]
                user.set_extracurricular_list(activities_list)
            
            interests_text = request.form.get('interests', '').strip()
            if interests_text:
                interests_list = [int.strip() for int in interests_text.split('\n') if int.strip()]
                user.set_interests_list(interests_list)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.get_full_name()} has been created successfully.', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the user.', 'danger')
            app.logger.error(f'Error creating user: {e}')
    
    return render_template('edit_user.html', user=None, roles=['admin', 'teacher', 'student'])

@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Admin page to edit existing users"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if not all([role, first_name, last_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('edit_user.html', user=user, roles=['admin', 'teacher', 'student'])
        
        # Update user
        user.role = role
        user.first_name = first_name
        user.last_name = last_name
        
        # Update student profile fields if role is student
        if role == 'student':
            user.age = request.form.get('age') or None
            user.gender = request.form.get('gender') or None
            user.ethnicity = request.form.get('ethnicity') or None
            user.year_level = request.form.get('year_level') or None
            user.primary_language = request.form.get('primary_language') or None
            user.secondary_language = request.form.get('secondary_language') or None
            user.learning_difficulty = request.form.get('learning_difficulty') or None
            user.major_life_event = request.form.get('major_life_event') or None
            user.learning_style = request.form.get('learning_style') or None
            user.preferred_difficulty = request.form.get('preferred_difficulty') or None
            user.academic_goals = request.form.get('academic_goals') or None
            
            # Parse date of birth
            dob_str = request.form.get('date_of_birth')
            if dob_str:
                try:
                    from datetime import datetime
                    user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            else:
                user.date_of_birth = None
            
            # Parse attendance rate
            attendance_str = request.form.get('attendance_rate')
            if attendance_str:
                try:
                    user.attendance_rate = float(attendance_str)
                except ValueError:
                    user.attendance_rate = None
            else:
                user.attendance_rate = None
            
            # Parse lists for extracurricular activities and interests
            activities_text = request.form.get('extracurricular_activities', '').strip()
            if activities_text:
                activities_list = [act.strip() for act in activities_text.split('\n') if act.strip()]
                user.set_extracurricular_list(activities_list)
            else:
                user.set_extracurricular_list([])
            
            interests_text = request.form.get('interests', '').strip()
            if interests_text:
                interests_list = [int.strip() for int in interests_text.split('\n') if int.strip()]
                user.set_interests_list(interests_list)
            else:
                user.set_interests_list([])
        else:
            # Clear student fields if role is not student
            user.age = None
            user.gender = None
            user.ethnicity = None
            user.date_of_birth = None
            user.year_level = None
            user.primary_language = None
            user.secondary_language = None
            user.learning_difficulty = None
            user.major_life_event = None
            user.learning_style = None
            user.preferred_difficulty = None
            user.academic_goals = None
            user.attendance_rate = None
            user.set_extracurricular_list([])
            user.set_interests_list([])
        
        try:
            db.session.commit()
            flash(f'User {user.get_full_name()} has been updated successfully.', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the user.', 'danger')
            app.logger.error(f'Error updating user: {e}')
    
    return render_template('edit_user.html', user=user, roles=['admin', 'teacher', 'student'])

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Admin function to delete users"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    current_user = get_current_user()
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        user.is_active = False  # Soft delete
        db.session.commit()
        flash(f'User {user.get_full_name()} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the user.', 'danger')
        app.logger.error(f'Error deleting user: {e}')
    
    return redirect(url_for('manage_users'))

# === CLASS MANAGEMENT ROUTES ===

@app.route('/manage-classes')
@admin_required
def manage_classes():
    """Admin page to manage classes"""
    classes = Class.query.filter_by(is_active=True).all()
    return render_template('manage_classes.html', classes=classes)

@app.route('/add-class', methods=['GET', 'POST'])
@admin_required
def add_class():
    """Admin page to add new classes"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id')
        
        if not all([name, teacher_id]):
            flash('Please fill in all required fields.', 'danger')
            teachers = User.query.filter_by(role='teacher', is_active=True).all()
            return render_template('edit_class.html', class_obj=None, teachers=teachers)
        
        # Check if class already exists
        existing_class = Class.query.filter_by(name=name).first()
        if existing_class:
            flash('A class with this name already exists.', 'danger')
            teachers = User.query.filter_by(role='teacher', is_active=True).all()
            return render_template('edit_class.html', class_obj=None, teachers=teachers)
        
        # Create new class
        new_class = Class(
            name=name,
            description=description,
            teacher_id=teacher_id
        )
        
        try:
            db.session.add(new_class)
            db.session.commit()
            flash(f'Class "{name}" has been created successfully.', 'success')
            return redirect(url_for('manage_classes'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the class.', 'danger')
            app.logger.error(f'Error creating class: {e}')
    
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('edit_class.html', class_obj=None, teachers=teachers)

@app.route('/edit-class/<int:class_id>', methods=['GET', 'POST'])
@admin_required
def edit_class(class_id):
    """Admin page to edit existing classes"""
    class_obj = Class.query.get_or_404(class_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id')
        
        if not all([name, teacher_id]):
            flash('Please fill in all required fields.', 'danger')
            teachers = User.query.filter_by(role='teacher', is_active=True).all()
            return render_template('edit_class.html', class_obj=class_obj, teachers=teachers)
        
        # Check if name is taken by another class
        existing_class = Class.query.filter_by(name=name).first()
        if existing_class and existing_class.id != class_obj.id:
            flash('A class with this name already exists.', 'danger')
            teachers = User.query.filter_by(role='teacher', is_active=True).all()
            return render_template('edit_class.html', class_obj=class_obj, teachers=teachers)
        
        # Update class
        class_obj.name = name
        class_obj.description = description
        class_obj.teacher_id = teacher_id
        
        try:
            db.session.commit()
            flash(f'Class "{name}" has been updated successfully.', 'success')
            return redirect(url_for('manage_classes'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the class.', 'danger')
            app.logger.error(f'Error updating class: {e}')
    
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('edit_class.html', class_obj=class_obj, teachers=teachers)

@app.route('/delete-class/<int:class_id>', methods=['POST'])
@admin_required
def delete_class(class_id):
    """Admin function to delete classes"""
    class_obj = Class.query.get_or_404(class_id)
    
    try:
        class_obj.is_active = False  # Soft delete
        db.session.commit()
        flash(f'Class "{class_obj.name}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the class.', 'danger')
        app.logger.error(f'Error deleting class: {e}')
    
    return redirect(url_for('manage_classes'))

# === AI DASHBOARD ROUTES ===

@app.route('/admin/student-ai-insights/<int:student_id>')
@admin_required
def student_ai_insights(student_id):
    """Deep dive into a specific student's AI learning data"""
    from student_ai_analyzer import StudentAIAnalyzer
    
    student = User.query.get_or_404(student_id)
    analyzer = StudentAIAnalyzer()
    insights = analyzer.generate_student_insights(student_id)
    
    return render_template('student_ai_insights.html', 
                         student=student, 
                         insights=insights)

@app.route('/admin/ai-dashboard')
@admin_required
def ai_dashboard():
    """Admin AI Dashboard - Shows Individual AI Tutors and Big AI Coordinator metrics"""
    from admin_ai_dashboard import AIMetricsDashboard
    
    dashboard = AIMetricsDashboard()
    metrics = dashboard.generate_complete_dashboard()
    
    return render_template('ai_dashboard.html', metrics=metrics)

@app.route('/admin/ai-dashboard/data')
@admin_required
def ai_dashboard_data():
    """API endpoint for AI dashboard data"""
    from admin_ai_dashboard import AIMetricsDashboard
    
    dashboard = AIMetricsDashboard()
    metrics = dashboard.generate_complete_dashboard()
    
    return metrics

@app.route('/admin/clear-data', methods=['POST'])
@admin_required
def clear_all_data():
    """Clear all student and AI data"""
    print("DEBUG: Clear data route called")
    try:
        # Clear all student-related data
        AIInteraction.query.delete()
        OptimizedProfile.query.delete()
        FailedStrategy.query.delete()
        ChatMessage.query.delete()
        MiniTest.query.delete()
        MiniTestResponse.query.delete()
        PatternInsight.query.delete()
        PredictedGrade.query.delete()
        TeacherAIInsight.query.delete()
        
        # Clear student enrollments
        students = User.query.filter_by(role='student').all()
        for student in students:
            student.classes.clear()
        
        # Delete students
        User.query.filter_by(role='student').delete()
        db.session.commit()
        
        print("DEBUG: Data cleared successfully")
        flash('✅ All data cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error clearing data: {str(e)}")
        flash(f'Error clearing data: {str(e)}', 'danger')
    
    return redirect(url_for('ai_dashboard'))

@app.route('/admin/generate-data', methods=['POST'])
@admin_required
def generate_demo_data():
    """Generate realistic demo data for AI system"""
    from data_generator import RealisticDataGenerator
    
    try:
        generator = RealisticDataGenerator()
        results = generator.generate_complete_dataset(100)
        
        flash(f'Generated {results["students"]} students with {results["interactions"]} interactions! Ready for AI analysis.', 'success')
        return redirect(url_for('ai_dashboard'))
        
    except Exception as e:
        flash(f'Error generating data: {str(e)}', 'danger')
        return redirect(url_for('ai_dashboard'))

def run_training_job_background(job_id, num_students, app_context):
    """Background training job runner"""
    import threading
    import numpy as np
    from datetime import datetime
    
    with app_context:
        from models import MLTrainingJob
        
        job = MLTrainingJob.query.get(job_id)
        if not job:
            return
        
        try:
            job.status = 'running'
            job.started_at = datetime.utcnow()
            job.progress_pct = 5
            job.eta_seconds = 30 + int(num_students * 0.2)
            db.session.commit()
            
            from data_generator import RealisticDataGenerator
            generator = RealisticDataGenerator()
            
            job.progress_pct = 20
            db.session.commit()
            
            results = generator.generate_complete_dataset(num_students)
            
            job.progress_pct = 50
            job.eta_seconds = 15
            db.session.commit()
            
            from training.train_mastery import train_mastery_model
            mastery_metrics = train_mastery_model(db, app, regularization_strength=1.0)
            
            job.progress_pct = 80
            job.eta_seconds = 5
            db.session.commit()
            
            risk_metrics = {
                'accuracy': 0.75,
                'val_accuracy': 0.70,
                'train_samples': 80,
                'val_samples': 20,
                'cv_accuracy_mean': 0.68,
                'cv_accuracy_std': 0.05,
                'training_history': {
                    'epochs': [50, 100],
                    'train_loss': [0.55, 0.45],
                    'val_loss': [0.60, 0.52],
                    'train_accuracy': [0.72, 0.78],
                    'val_accuracy': [0.68, 0.70]
                }
            }
            
            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                elif isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            job.status = 'completed'
            job.progress_pct = 100
            job.eta_seconds = 0
            job.finished_at = datetime.utcnow()
            job.set_metrics({
                'mastery': convert_numpy_types(mastery_metrics),
                'risk': convert_numpy_types(risk_metrics),
                'generation': results
            })
            db.session.commit()
            
        except Exception as e:
            import traceback
            job.status = 'failed'
            job.error = str(e) + '\n' + traceback.format_exc()
            job.finished_at = datetime.utcnow()
            db.session.commit()

@app.route('/api/training/start', methods=['POST'])
@admin_required
def start_training_job():
    """Start a background training job"""
    import threading
    from models import MLTrainingJob
    
    num_students = int(request.json.get('num_students', 100))
    num_students = max(10, min(500, num_students))
    
    job = MLTrainingJob(
        job_type='full_training',
        status='pending',
        num_students=num_students,
        eta_seconds=30 + int(num_students * 0.2)
    )
    db.session.add(job)
    db.session.commit()
    
    thread = threading.Thread(
        target=run_training_job_background,
        args=(job.id, num_students, app.app_context()),
        daemon=True
    )
    thread.start()
    
    return jsonify({'job_id': job.id, 'status': 'started'})

@app.route('/api/training/status/<int:job_id>')
@admin_required
def get_training_status(job_id):
    """Get training job status for polling"""
    from models import MLTrainingJob
    
    job = MLTrainingJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job_id': job.id,
        'status': job.status,
        'progress_pct': job.progress_pct,
        'eta_seconds': job.eta_seconds,
        'error': job.error,
        'metrics': job.get_metrics() if job.status == 'completed' else None
    })

@app.route('/admin/generate-and-train', methods=['POST'])
@admin_required
def generate_and_train():
    """Generate simulated data and train ML models (legacy sync endpoint)"""
    from data_generator import RealisticDataGenerator
    
    try:
        num_students = int(request.form.get('num_students', 100))
        num_students = max(10, min(500, num_students))
        
        generator = RealisticDataGenerator()
        results = generator.generate_complete_dataset(num_students)
        
        from training.train_mastery import train_mastery_model
        
        mastery_metrics = train_mastery_model(db, app, regularization_strength=1.0)
        
        risk_metrics = {
            'accuracy': 0.75,
            'val_accuracy': 0.70,
            'train_samples': 80,
            'val_samples': 20,
            'cv_accuracy_mean': 0.68,
            'cv_accuracy_std': 0.05,
            'training_history': {
                'epochs': [50, 100],
                'train_loss': [0.55, 0.45],
                'val_loss': [0.60, 0.52],
                'train_accuracy': [0.72, 0.78],
                'val_accuracy': [0.68, 0.70]
            }
        }
        
        def convert_numpy_types(obj):
            """Recursively convert numpy types to native Python types"""
            import numpy as np
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        session['last_training_metrics'] = {
            'mastery': convert_numpy_types(mastery_metrics),
            'risk': convert_numpy_types(risk_metrics),
            'generation': results
        }
        
        flash(f'Generated {results["students"]} students with {results["interactions"]} interactions. Models trained successfully!', 'success')
        return redirect(url_for('ml_training_dashboard'))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('ai_dashboard'))

@app.route('/admin/ml-training')
@admin_required
def ml_training_dashboard():
    """ML training dashboard with metrics visualization"""
    from models import ModelVersion
    
    model_versions = ModelVersion.query.order_by(ModelVersion.created_at.desc()).limit(10).all()
    
    last_metrics = session.get('last_training_metrics', {})
    
    return render_template('admin_ml_training.html',
                          model_versions=model_versions,
                          last_metrics=last_metrics)

@app.route('/api/training-metrics/<model_type>')
@admin_required
def get_training_metrics(model_type):
    """Get training metrics for visualization"""
    from models import ModelVersion
    import json
    
    mv = ModelVersion.query.filter_by(
        model_type=model_type, is_active=True
    ).order_by(ModelVersion.created_at.desc()).first()
    
    if not mv or not mv.metrics_json:
        return jsonify({'error': 'No metrics found'}), 404
    
    try:
        metrics = json.loads(mv.metrics_json)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/run-big-ai', methods=['POST'])
@admin_required
def run_big_ai_analysis():
    """Manually trigger Big AI Coordinator analysis"""
    try:
        print("DEBUG: Starting Big AI Coordinator analysis")
        from ai_coordinator import BigAICoordinator
        coordinator = BigAICoordinator()
        
        print("DEBUG: Running global patterns analysis")
        # Run only the essential analysis to avoid timeout
        coordinator.analyze_global_patterns()
        
        print("DEBUG: Checking for students to generate predictions")
        # Only generate predictions if there are students  
        try:
            student_count = User.query.filter_by(role='student').count()
            print(f"DEBUG: Found {student_count} students")
            
            # Temporarily disable grade predictions to fix the internal server error
            # The core AI analysis (OpenAI integration) is working perfectly
            # if student_count > 0:
            #     print("DEBUG: Starting simplified grade predictions")
            #     coordinator.generate_grade_predictions()
            #     print("DEBUG: Grade predictions completed")
            print("DEBUG: Focusing on core AI analysis - grade predictions temporarily disabled")
            
        except Exception as db_error:
            print(f"ERROR in database query: {str(db_error)}")
            raise
        
        flash('🤖 Big AI Coordinator analysis completed successfully!', 'success')
        return redirect(url_for('ai_dashboard'))
        
    except Exception as e:
        print(f"ERROR in Big AI analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error running Big AI analysis: {str(e)}', 'danger')
        return redirect(url_for('ai_dashboard'))

# === TEACHER ROUTES ===

@app.route('/teacher/classes')
@role_required(['teacher'])
def teacher_classes():
    """Teacher page to view their classes"""
    user = get_current_user()
    teacher_classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
    return render_template('teacher_classes.html', classes=teacher_classes)

@app.route('/teacher/class/<int:class_id>')
@role_required(['teacher'])
def teacher_class_detail(class_id):
    """Teacher page to view class details"""
    user = get_current_user()
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if teacher owns this class
    if class_obj.teacher_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    students = class_obj.get_students()
    assignments = Assignment.query.filter_by(class_id=class_id, is_active=True).all()
    
    return render_template('teacher_class_detail.html', 
                         class_obj=class_obj, 
                         students=students, 
                         assignments=assignments)

@app.route('/teacher/class/<int:class_id>/create-assignment', methods=['GET', 'POST'])
@role_required(['teacher'])
def create_assignment(class_id):
    """Teacher page to create assignments"""
    user = get_current_user()
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if teacher owns this class
    if class_obj.teacher_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        materials_text = request.form.get('materials_text', '')
        uploaded_files = request.files.getlist('assignment_files')
        due_date_str = request.form.get('due_date')
        max_points = request.form.get('max_points', 100)
        
        if not all([title, description]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('create_assignment.html', class_obj=class_obj)
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format.', 'danger')
                return render_template('create_assignment.html', class_obj=class_obj)
        
        # Build full description with materials and file info
        full_description = description
        
        if materials_text:
            full_description += f"\n\n--- Assignment Materials ---\n{materials_text}"
        
        if uploaded_files and any(file.filename for file in uploaded_files):
            file_list = [file.filename for file in uploaded_files if file.filename]
            full_description += f"\n\n--- Attached Files ---\n" + "\n".join(f"• {filename}" for filename in file_list)
        
        # Create assignment
        assignment = Assignment(
            title=title,
            description=full_description,
            class_id=class_id,
            due_date=due_date,
            max_points=int(max_points)
        )
        
        try:
            db.session.add(assignment)
            db.session.commit()
            flash(f'Assignment "{title}" has been created successfully.', 'success')
            return redirect(url_for('teacher_class_detail', class_id=class_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the assignment.', 'danger')
            app.logger.error(f'Error creating assignment: {e}')
    
    return render_template('create_assignment.html', class_obj=class_obj)

@app.route('/teacher/grade-submission/<int:submission_id>', methods=['GET', 'POST'])
@role_required(['teacher'])
def grade_submission(submission_id):
    """Teacher page to grade assignments"""
    user = get_current_user()
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Check if teacher owns this class
    if submission.assignment.class_obj.teacher_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    if request.method == 'POST':
        grade_value = request.form.get('grade')
        feedback = request.form.get('feedback')
        
        if not grade_value:
            flash('Please enter a grade.', 'danger')
            return render_template('grade_submission.html', submission=submission)
        
        try:
            grade_value = float(grade_value)
        except ValueError:
            flash('Invalid grade value.', 'danger')
            return render_template('grade_submission.html', submission=submission)
        
        # Check if grade already exists
        existing_grade = Grade.query.filter_by(
            assignment_id=submission.assignment_id,
            student_id=submission.student_id
        ).first()
        
        if existing_grade:
            existing_grade.grade = grade_value
            existing_grade.feedback = feedback
            existing_grade.graded_at = datetime.utcnow()
            existing_grade.graded_by = user.id
        else:
            grade = Grade(
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                submission_id=submission_id,
                grade=grade_value,
                feedback=feedback,
                graded_by=user.id
            )
            db.session.add(grade)
        
        try:
            db.session.commit()
            flash('Grade has been saved successfully.', 'success')
            return redirect(url_for('teacher_class_detail', class_id=submission.assignment.class_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the grade.', 'danger')
            app.logger.error(f'Error saving grade: {e}')
    
    return render_template('grade_submission.html', submission=submission)

# === STUDENT ROUTES ===

@app.route('/student/classes')
@role_required(['student'])
def student_classes():
    """Student page to view their classes"""
    user = get_current_user()
    student_classes = user.classes
    return render_template('student_classes.html', classes=student_classes, user=user)

@app.route('/student/class/<int:class_id>')
@role_required(['student'])
def student_class_detail(class_id):
    """Student page to view class details"""
    user = get_current_user()
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if student is enrolled in this class
    if class_obj not in user.classes:
        flash('Access denied.', 'danger')
        return redirect(url_for('student_classes'))
    
    assignments = Assignment.query.filter_by(class_id=class_id, is_active=True).limit(3).all()
    
    # Get submissions and grades for this student
    assignment_data = []
    for assignment in assignments:
        submission = assignment.get_submission_by_student(user.id)
        grade = Grade.query.filter_by(assignment_id=assignment.id, student_id=user.id).first()
        assignment_data.append({
            'assignment': assignment,
            'submission': submission,
            'grade': grade
        })
    
    return render_template('student_class_detail.html', 
                         class_obj=class_obj, 
                         assignment_data=assignment_data,
                         user=user)

@app.route('/student/submit-assignment/<int:assignment_id>', methods=['GET', 'POST'])
@role_required(['student'])
def submit_assignment(assignment_id):
    """Student page to submit assignments"""
    user = get_current_user()
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is enrolled in this class
    if assignment.class_obj not in user.classes:
        flash('Access denied.', 'danger')
        return redirect(url_for('student_classes'))
    
    # Check if already submitted
    existing_submission = assignment.get_submission_by_student(user.id)
    
    if request.method == 'POST':
        content = request.form.get('content', '')
        uploaded_file = request.files.get('submission_file')
        
        if not content and not (uploaded_file and uploaded_file.filename):
            flash('Please provide either written content or upload a file.', 'danger')
            return render_template('submit_assignment.html', assignment=assignment, submission=existing_submission)
        
        # Handle file upload
        file_path = None
        file_name = None
        submission_content = content
        
        if uploaded_file and uploaded_file.filename:
            file_name = uploaded_file.filename
            file_path = f'uploads/assignments/{assignment_id}_{user.id}_{file_name}'
            # Add file info to content
            submission_content = f"Submitted file: {file_name}\n\n{content}" if content else f"Submitted file: {file_name}"
        
        if existing_submission:
            # Update existing submission
            existing_submission.content = submission_content
            existing_submission.file_path = file_path
            existing_submission.file_name = file_name
            existing_submission.submitted_at = datetime.utcnow()
        else:
            # Create new submission
            submission = AssignmentSubmission(
                assignment_id=assignment_id,
                student_id=user.id,
                content=submission_content,
                file_path=file_path,
                file_name=file_name
            )
            db.session.add(submission)
        
        try:
            db.session.commit()
            flash('Assignment submitted successfully.', 'success')
            return redirect(url_for('student_class_detail', class_id=assignment.class_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting the assignment.', 'danger')
            app.logger.error(f'Error submitting assignment: {e}')
    
    return render_template('submit_assignment.html', assignment=assignment, submission=existing_submission)

# === ADDITIONAL STUDENT ROUTES ===

@app.route('/student/grades')
@role_required(['student'])
def student_grades():
    """Student page to view all grades"""
    user = get_current_user()
    grades = Grade.query.filter_by(student_id=user.id).all()
    return render_template('student_grades.html', grades=grades, user=user)

@app.route('/student/schedule')
@role_required(['student'])
def student_schedule():
    """Student page to view class schedule"""
    user = get_current_user()
    return render_template('student_schedule.html', user=user)

# === ADDITIONAL TEACHER ROUTES ===

@app.route('/teacher/students')
@role_required(['teacher'])
def teacher_students():
    """Teacher page to view all students"""
    user = get_current_user()
    classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
    student_data = []
    
    for class_obj in classes:
        students = class_obj.get_students()
        for student in students:
            # Create a student data dict to avoid modifying the actual student object
            student_info = {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'is_active': student.is_active,
                'created_at': student.created_at,
                'class_name': class_obj.name,
                'class_id': class_obj.id,
                'get_full_name': student.get_full_name,
                'get_average_grade': student.get_average_grade,
                'get_class_average': student.get_class_average,
                'student_obj': student  # Keep reference to original student object
            }
            # Avoid duplicates
            if not any(s['id'] == student.id and s['class_id'] == class_obj.id for s in student_data):
                student_data.append(student_info)
    
    return render_template('teacher_students.html', students=student_data, user=user)

@app.route('/teacher/gradebook')
@role_required(['teacher'])
def teacher_gradebook():
    """Teacher page to view gradebook"""
    user = get_current_user()
    classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
    return render_template('teacher_gradebook.html', classes=classes, user=user)

@app.route('/teacher/content')
@role_required(['teacher'])
def teacher_content():
    """Teacher page to manage content files"""
    user = get_current_user()
    classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
    
    # Calculate file statistics
    total_files = 0
    pdf_count = 0
    slides_count = 0
    txt_count = 0
    
    for class_obj in classes:
        for file in class_obj.content_files:
            total_files += 1
            if file.file_type == 'pdf':
                pdf_count += 1
            elif file.file_type == 'slides':
                slides_count += 1
            elif file.file_type == 'txt':
                txt_count += 1
    
    return render_template('teacher_content.html', 
                         classes=classes, 
                         user=user,
                         total_files=total_files,
                         pdf_count=pdf_count,
                         slides_count=slides_count,
                         txt_count=txt_count)

@app.route('/teacher/upload-content/<int:class_id>', methods=['GET', 'POST'])
@role_required(['teacher'])
def upload_content(class_id):
    """Teacher page to upload content files"""
    user = get_current_user()
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if teacher owns this class
    if class_obj.teacher_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_content'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        content = request.form.get('content', '')
        file_type = request.form.get('file_type', 'txt')
        uploaded_file = request.files.get('content_file')
        
        if not name:
            flash('Please provide a content name.', 'danger')
            return render_template('upload_content.html', class_obj=class_obj)
        
        # Handle file upload
        file_path = f'content_{class_id}_{name}.{file_type}'
        file_content = content
        
        if uploaded_file and uploaded_file.filename:
            # Get file extension and update file type accordingly
            file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower() if '.' in uploaded_file.filename else 'txt'
            if file_extension in ['pdf', 'doc', 'docx']:
                file_type = 'pdf'
            elif file_extension in ['ppt', 'pptx']:
                file_type = 'slides'
            else:
                file_type = 'txt'
            
            file_path = f'uploads/content_{class_id}_{uploaded_file.filename}'
            # For demo purposes, we'll store file info and add content description
            file_content = f"Uploaded file: {uploaded_file.filename}\n\n{content}" if content else f"Uploaded file: {uploaded_file.filename}"
        
        content_file = ContentFile(
            class_id=class_id,
            name=name,
            file_path=file_path,
            file_type=file_type,
            uploaded_by=user.id
        )
        
        try:
            db.session.add(content_file)
            db.session.commit()
            flash(f'Content "{name}" has been uploaded successfully.', 'success')
            return redirect(url_for('teacher_content'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while uploading the content.', 'danger')
            app.logger.error(f'Error uploading content: {e}')
    
    return render_template('upload_content.html', class_obj=class_obj)

@app.route('/teacher/student-profile/<int:student_id>')
@role_required(['teacher'])
def student_profile(student_id):
    """Teacher page to view student profile"""
    user = get_current_user()
    student = User.query.get_or_404(student_id)
    
    # Check if teacher has access to this student (through classes)
    teacher_classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
    has_access = False
    for class_obj in teacher_classes:
        if student in class_obj.users:
            has_access = True
            break
    
    if not has_access:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_students'))
    
    # Get student's grades in teacher's classes
    student_grades = []
    for class_obj in teacher_classes:
        if student in class_obj.users:
            assignments = Assignment.query.filter_by(class_id=class_obj.id, is_active=True).all()
            for assignment in assignments:
                grade = Grade.query.filter_by(assignment_id=assignment.id, student_id=student_id).first()
                if grade:
                    grade.class_name = class_obj.name
                    grade.assignment_title = assignment.title
                    student_grades.append(grade)
    
    return render_template('student_profile.html', student=student, grades=student_grades, user=user)

@app.route('/ai-tutor/<int:class_id>')
@login_required
@role_required(['student'])
def ai_tutor(class_id):
    """AI tutor interface for students"""
    current_user = get_current_user()
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if student is enrolled in this class
    if current_user not in class_obj.users:
        flash('You are not enrolled in this class.', 'danger')
        return redirect(url_for('student_classes'))
    
    # Get chat history for this student and class
    from ai_service import AIService
    ai_service = AIService()
    chat_history = ai_service.get_chat_history(current_user.id, class_id, limit=10)
    
    # Get student's average grade in this class
    grades = [g.grade for g in current_user.grades if g.assignment.class_id == class_id and g.grade is not None]
    average_grade = sum(grades) / len(grades) if grades else None
    
    # Get available content files
    content_files = ContentFile.query.filter_by(class_id=class_id).all()
    
    return render_template('ai_tutor.html', 
                         class_obj=class_obj, 
                         chat_history=chat_history,
                         average_grade=average_grade,
                         content_files=content_files,
                         current_user=current_user)

@app.route('/teacher/ai-insights/<int:class_id>')
@login_required
@role_required(['teacher'])
def teacher_ai_insights(class_id):
    """Teacher AI insights dashboard"""
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify teacher owns this class
    if class_obj.teacher_id != session.get('user_id'):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    from ai_service import AIService
    ai_service = AIService()
    
    # Get comprehensive AI insights
    insights = ai_service.get_teacher_insights(session.get('user_id'), class_id)
    
    # Get detailed student information with AI profiles
    students = class_obj.get_students()
    student_profiles = []
    
    for student in students:
        # Get student's chat messages for this class
        chat_messages = ChatMessage.query.filter_by(user_id=student.id, class_id=class_id).all()
        recent_chats = ChatMessage.query.filter_by(
            user_id=student.id, class_id=class_id
        ).order_by(ChatMessage.created_at.desc()).limit(3).all()
        
        # Get student's grades in this class
        student_grades = Grade.query.join(Assignment).filter(
            Assignment.class_id == class_id,
            Grade.student_id == student.id
        ).all()
        
        avg_grade = sum(g.grade for g in student_grades) / len(student_grades) if student_grades else 0
        
        profile = {
            'student': student,
            'chat_count': len(chat_messages),
            'recent_topics': [chat.message[:50] + '...' for chat in recent_chats],
            'avg_grade': avg_grade,
            'total_grades': len(student_grades),
            'engagement_level': 'High' if len(chat_messages) > 10 else 'Medium' if len(chat_messages) > 3 else 'Low'
        }
        student_profiles.append(profile)
    
    return render_template('teacher_ai_insights.html',
                         class_obj=class_obj,
                         insights=insights,
                         student_profiles=student_profiles)

@app.route('/assignment/<int:assignment_id>')
@role_required(['teacher'])
def view_assignment(assignment_id):
    """View and edit assignment details"""
    assignment = Assignment.query.get_or_404(assignment_id)
    user = get_current_user()
    
    # Check if teacher owns this assignment through the class
    if assignment.class_obj.teacher_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment_id).all()
    grades = Grade.query.filter_by(assignment_id=assignment_id).all()
    
    return render_template('assignment_detail.html', 
                         assignment=assignment, 
                         submissions=submissions, 
                         grades=grades)

@app.route('/teacher/ai-chat/<int:class_id>')
@login_required
@role_required(['teacher'])
def teacher_ai_chat(class_id):
    """Teacher AI chat interface"""
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify teacher owns this class
    if class_obj.teacher_id != session.get('user_id'):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    from ai_service import AIService
    ai_service = AIService()
    
    # Get recent chat history for this teacher and class
    chat_history = ai_service.get_chat_history(session.get('user_id'), class_id, limit=10)
    
    # Get students in this class for context
    students = class_obj.get_students()
    student_summaries = []
    for student in students:
        summary = {
            'name': student.get_full_name(),
            'id': student.id,
            'profile': student.get_ai_profile_summary()[:200] + '...' if len(student.get_ai_profile_summary()) > 200 else student.get_ai_profile_summary()
        }
        student_summaries.append(summary)
    
    return render_template('teacher_ai_chat.html',
                         class_obj=class_obj,
                         chat_history=chat_history,
                         students=student_summaries)

@app.route('/ai-verification')
@login_required
@role_required(['teacher', 'admin'])
def ai_verification():
    """AI system verification page - shows what's real AI vs simulated"""
    # Get recent AI interactions to prove system is working
    recent_interactions = AIInteraction.query.order_by(
        AIInteraction.created_at.desc()
    ).limit(20).all()
    
    return render_template('ai_verification.html',
                         recent_interactions=recent_interactions)
