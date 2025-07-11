from flask import jsonify, request, session, send_file
from app import app, db
from models import User, Class, ChatMessage, AIModel, StudentProfile, Assignment, AssignmentSubmission, Grade, ContentFile, TokenUsage
from ai_service import AIService
from auth import login_required, role_required
import csv
import io
import json
from datetime import datetime

ai_service = AIService()

# AI Chatbot Routes
@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Send a message to the AI chatbot"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        class_id = data.get('class_id')
        
        if not message or not class_id:
            return jsonify({'error': 'Message and class_id are required'}), 400
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role != 'student':
            return jsonify({'error': 'Only students can send chat messages'}), 403
        
        # Check if student is enrolled in the class
        class_obj = Class.query.get(class_id)
        if not class_obj or user not in class_obj.users:
            return jsonify({'error': 'You are not enrolled in this class'}), 403
        
        # Generate AI response
        response = ai_service.generate_response(message, user_id, class_id)
        
        # Get token usage for this user today
        from datetime import date
        today = date.today()
        usage = TokenUsage.query.filter_by(user_id=user_id, date=today).first()
        tokens_used = usage.tokens_used if usage else 0
        
        return jsonify({
            'success': True,
            'message': message,
            'response': response,
            'tokens_used': tokens_used,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<int:class_id>')
@login_required
def get_chat_history(class_id):
    """Get chat history for a class"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'student':
            # Students can only see their own chat history
            messages = ai_service.get_chat_history(user_id, class_id)
        elif user.role == 'teacher':
            # Teachers can see all student chats in their classes
            class_obj = Class.query.get(class_id)
            if not class_obj or class_obj.teacher_id != user_id:
                return jsonify({'error': 'Access denied'}), 403
            
            messages = ai_service.get_all_chat_data(user_id, class_id)
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'messages': messages})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teacher/insights/<int:class_id>')
@login_required
@role_required(['teacher'])
def get_teacher_insights(class_id):
    """Get AI-generated insights about students for teachers"""
    try:
        user_id = session.get('user_id')
        insights = ai_service.get_teacher_insights(user_id, class_id)
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard Statistics Routes
@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics based on user role"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            stats = {
                'total_students': User.query.filter_by(role='student').count(),
                'total_teachers': User.query.filter_by(role='teacher').count(),
                'total_classes': Class.query.count(),
                'total_assignments': Assignment.query.count(),
                'total_chat_messages': ChatMessage.query.count(),
                'active_ai_models': AIModel.query.filter_by(is_active=True).count()
            }
        elif user.role == 'teacher':
            teacher_classes = Class.query.filter_by(teacher_id=user_id).all()
            total_students = sum(len(cls.get_students()) for cls in teacher_classes)
            pending_grades = Grade.query.join(Assignment).filter(
                Assignment.class_id.in_([cls.id for cls in teacher_classes]),
                Grade.grade.is_(None)
            ).count()
            
            stats = {
                'my_classes': len(teacher_classes),
                'total_students': total_students,
                'pending_grades': pending_grades,
                'total_assignments': Assignment.query.filter(
                    Assignment.class_id.in_([cls.id for cls in teacher_classes])
                ).count(),
                'chat_interactions': ChatMessage.query.filter(
                    ChatMessage.class_id.in_([cls.id for cls in teacher_classes])
                ).count()
            }
        elif user.role == 'student':
            student_classes = user.classes
            stats = {
                'enrolled_classes': len(student_classes),
                'total_assignments': Assignment.query.filter(
                    Assignment.class_id.in_([cls.id for cls in student_classes])
                ).count(),
                'submitted_assignments': AssignmentSubmission.query.filter_by(student_id=user_id).count(),
                'average_grade': user.get_average_grade(),
                'chat_interactions': ChatMessage.query.filter_by(user_id=user_id).count()
            }
        else:
            return jsonify({'error': 'Invalid user role'}), 403
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Data Export Routes for Admin
@app.route('/api/admin/export/preview', methods=['POST'])
@login_required
@role_required(['admin'])
def preview_export_data():
    """Preview what data will be exported based on selections"""
    try:
        data = request.get_json()
        selections = data.get('selections', {})
        
        export_tree = build_export_tree(selections)
        
        return jsonify({
            'export_tree': export_tree,
            'total_records': count_export_records(export_tree)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/export/download', methods=['POST'])
@login_required
@role_required(['admin'])
def download_export_data():
    """Download selected data as CSV"""
    try:
        data = request.get_json()
        selections = data.get('selections', {})
        
        # Generate CSV data
        csv_data = generate_csv_export(selections)
        
        # Create in-memory file
        output = io.StringIO()
        output.write(csv_data)
        output.seek(0)
        
        # Convert to bytes
        mem_file = io.BytesIO()
        mem_file.write(output.getvalue().encode('utf-8'))
        mem_file.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'school_data_export_{timestamp}.csv'
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def build_export_tree(selections):
    """Build a tree structure showing what data will be exported"""
    tree = {}
    
    if selections.get('users'):
        users = User.query.all()
        tree['users'] = {
            'count': len(users),
            'fields': ['id', 'email', 'role', 'first_name', 'last_name', 'age', 'learning_style', 'interests'],
            'related_data': {}
        }
        
        if selections.get('include_chat_history'):
            chat_count = ChatMessage.query.join(User).filter(
                User.id.in_([u.id for u in users])
            ).count()
            tree['users']['related_data']['chat_messages'] = {
                'count': chat_count,
                'fields': ['message', 'response', 'created_at', 'class_name']
            }
        
        if selections.get('include_grades'):
            grade_count = Grade.query.join(User).filter(
                User.id.in_([u.id for u in users])
            ).count()
            tree['users']['related_data']['grades'] = {
                'count': grade_count,
                'fields': ['grade', 'feedback', 'assignment_name', 'class_name']
            }
        
        if selections.get('include_assignments'):
            assignment_count = AssignmentSubmission.query.join(User).filter(
                User.id.in_([u.id for u in users])
            ).count()
            tree['users']['related_data']['assignments'] = {
                'count': assignment_count,
                'fields': ['assignment_name', 'submitted_at', 'content', 'file_name']
            }
    
    if selections.get('classes'):
        classes = Class.query.all()
        tree['classes'] = {
            'count': len(classes),
            'fields': ['id', 'name', 'description', 'subject', 'teacher_name'],
            'related_data': {}
        }
        
        if selections.get('include_content_files'):
            content_count = ContentFile.query.filter(
                ContentFile.class_id.in_([c.id for c in classes])
            ).count()
            tree['classes']['related_data']['content_files'] = {
                'count': content_count,
                'fields': ['name', 'file_type', 'uploaded_at', 'uploader_name']
            }
    
    if selections.get('ai_models'):
        ai_models = AIModel.query.all()
        tree['ai_models'] = {
            'count': len(ai_models),
            'fields': ['subject', 'model_name', 'prompt_template', 'created_at']
        }
    
    return tree

def count_export_records(tree):
    """Count total records that will be exported"""
    total = 0
    
    for category, data in tree.items():
        total += data.get('count', 0)
        if 'related_data' in data:
            for related_category, related_data in data['related_data'].items():
                total += related_data.get('count', 0)
    
    return total

def generate_csv_export(selections):
    """Generate CSV data based on selections"""
    output = io.StringIO()
    
    if selections.get('users'):
        # Export users
        users = User.query.all()
        writer = csv.writer(output)
        
        # Write header
        header = ['User ID', 'Email', 'Role', 'First Name', 'Last Name', 'Age', 'Learning Style', 'Interests', 'Academic Goals']
        
        if selections.get('include_chat_history'):
            header.extend(['Chat Messages Count', 'Recent Chat Topics'])
        
        if selections.get('include_grades'):
            header.extend(['Average Grade', 'Total Grades'])
        
        writer.writerow(header)
        
        # Write data
        for user in users:
            row = [
                user.id,
                user.email,
                user.role,
                user.first_name,
                user.last_name,
                user.age,
                user.learning_style,
                ', '.join(user.get_interests_list()),
                user.academic_goals
            ]
            
            if selections.get('include_chat_history'):
                chat_count = ChatMessage.query.filter_by(user_id=user.id).count()
                recent_chats = ChatMessage.query.filter_by(user_id=user.id).order_by(
                    ChatMessage.created_at.desc()
                ).limit(3).all()
                recent_topics = '; '.join([chat.message[:50] for chat in recent_chats])
                row.extend([chat_count, recent_topics])
            
            if selections.get('include_grades'):
                avg_grade = user.get_average_grade()
                total_grades = len(user.grades)
                row.extend([avg_grade, total_grades])
            
            writer.writerow(row)
        
        output.write('\n\n')
    
    if selections.get('classes'):
        # Export classes
        classes = Class.query.all()
        writer = csv.writer(output)
        
        writer.writerow(['Class ID', 'Name', 'Description', 'Subject', 'Teacher', 'Student Count', 'AI Model'])
        
        for class_obj in classes:
            writer.writerow([
                class_obj.id,
                class_obj.name,
                class_obj.description,
                class_obj.subject,
                class_obj.teacher.get_full_name(),
                class_obj.get_student_count(),
                class_obj.ai_model.subject if class_obj.ai_model else 'None'
            ])
        
        output.write('\n\n')
    
    if selections.get('chat_history'):
        # Export chat history
        messages = ChatMessage.query.join(User).join(Class).all()
        writer = csv.writer(output)
        
        writer.writerow(['Message ID', 'Student Name', 'Class Name', 'Message', 'AI Response', 'Created At'])
        
        for msg in messages:
            writer.writerow([
                msg.id,
                msg.user.get_full_name(),
                msg.class_obj.name,
                msg.message,
                msg.response,
                msg.created_at.isoformat()
            ])
    
    return output.getvalue()

# API Routes for React Components
@app.route('/api/classes')
@login_required
def get_classes():
    """Get classes based on user role"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            classes = Class.query.all()
        elif user.role == 'teacher':
            classes = Class.query.filter_by(teacher_id=user_id).all()
        elif user.role == 'student':
            classes = user.classes
        else:
            return jsonify({'error': 'Invalid user role'}), 403
        
        classes_data = []
        for cls in classes:
            class_data = {
                'id': cls.id,
                'name': cls.name,
                'description': cls.description,
                'subject': cls.subject,
                'teacher_name': cls.teacher.get_full_name(),
                'student_count': cls.get_student_count(),
                'has_ai_model': cls.ai_model is not None,
                'ai_model_subject': cls.ai_model.subject if cls.ai_model else None
            }
            classes_data.append(class_data)
        
        return jsonify({'classes': classes_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students')
@login_required
@role_required(['admin', 'teacher'])
def get_students():
    """Get students based on user role"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            students = User.query.filter_by(role='student').all()
        elif user.role == 'teacher':
            # Get students from teacher's classes
            teacher_classes = Class.query.filter_by(teacher_id=user_id).all()
            students = []
            for cls in teacher_classes:
                students.extend(cls.get_students())
            # Remove duplicates
            students = list(set(students))
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        students_data = []
        for student in students:
            student_data = {
                'id': student.id,
                'name': student.get_full_name(),
                'email': student.email,
                'age': student.age,
                'learning_style': student.learning_style,
                'interests': student.get_interests_list(),
                'average_grade': student.get_average_grade(),
                'chat_interactions': ChatMessage.query.filter_by(user_id=student.id).count(),
                'enrolled_classes': len(student.classes)
            }
            students_data.append(student_data)
        
        return jsonify({'students': students_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/token-usage')
@login_required
def get_token_usage():
    """Get current daily token usage for user"""
    try:
        user_id = session.get('user_id')
        from datetime import date
        today = date.today()
        
        usage = TokenUsage.query.filter_by(user_id=user_id, date=today).first()
        tokens_used = usage.tokens_used if usage else 0
        requests_made = usage.requests_made if usage else 0
        
        return jsonify({
            'success': True,
            'tokens_used': tokens_used,
            'requests_made': requests_made,
            'daily_limit': 10000
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500