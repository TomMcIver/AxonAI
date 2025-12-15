from flask import jsonify, request, session, send_file
from app import app, db
from models import User, Class, ChatMessage, AIModel, StudentProfile, Assignment, AssignmentSubmission, Grade, ContentFile, TokenUsage, MiniTest, MiniTestResponse, OptimizedProfile
from ai_service import AIService
from auth import login_required, role_required
import csv
import io
import json
import random
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

@app.route('/api/chat', methods=['POST'])
@login_required
def send_chat_message_unified():
    """Unified chat endpoint for both students and teachers"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        class_id = data.get('class_id')
        message_type = data.get('message_type', 'student')
        
        if not message or not class_id:
            return jsonify({'success': False, 'error': 'Missing message or class_id'})
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        # Get class and verify access
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return jsonify({'success': False, 'error': 'Class not found'})
        
        # Verify access based on role
        if user.role == 'student':
            if user not in class_obj.users:
                return jsonify({'success': False, 'error': 'Not enrolled in this class'})
            # Generate student tutoring response
            response = ai_service.generate_response(message, user_id, class_id)
        elif user.role == 'teacher':
            if class_obj.teacher_id != user_id:
                return jsonify({'success': False, 'error': 'Access denied'})
            # Generate teacher insights response
            response = ai_service.generate_teacher_response(message, user_id, class_id)
        else:
            return jsonify({'success': False, 'error': 'Invalid user role'})
        
        if response:
            return jsonify({
                'success': True, 
                'response': response,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate response'})
            
    except Exception as e:
        app.logger.error(f'Chat API error: {e}')
        return jsonify({'success': False, 'error': 'Internal server error'})

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
            'fields': ['id', 'role', 'first_name', 'last_name', 'age', 'learning_style', 'interests'],
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
        header = ['User ID', 'Role', 'First Name', 'Last Name', 'Age', 'Learning Style', 'Interests', 'Academic Goals']
        
        if selections.get('include_chat_history'):
            header.extend(['Chat Messages Count', 'Recent Chat Topics'])
        
        if selections.get('include_grades'):
            header.extend(['Average Grade', 'Total Grades'])
        
        writer.writerow(header)
        
        # Write data
        for user in users:
            row = [
                user.id,
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

# Question bank for quiz generation
QUESTION_BANK = {
    'math': {
        'algebra': [
            {'q': 'Solve for x: 2x + 5 = 13', 'a': '4', 'choices': ['3', '4', '5', '6']},
            {'q': 'Solve for x: 3x - 7 = 8', 'a': '5', 'choices': ['3', '4', '5', '6']},
            {'q': 'Solve for x: x/2 + 3 = 7', 'a': '8', 'choices': ['6', '7', '8', '9']},
            {'q': 'What is x if 4x = 20?', 'a': '5', 'choices': ['4', '5', '6', '7']},
            {'q': 'If 2x + 3 = 11, what is x?', 'a': '4', 'choices': ['2', '3', '4', '5']},
        ],
        'geometry': [
            {'q': 'Area of a rectangle with length 5 and width 3?', 'a': '15', 'choices': ['12', '13', '15', '16']},
            {'q': 'Perimeter of a square with side 4?', 'a': '16', 'choices': ['12', '14', '16', '18']},
            {'q': 'Sum of angles in a triangle?', 'a': '180', 'choices': ['90', '180', '270', '360']},
            {'q': 'Area of a triangle: base=6, height=4?', 'a': '12', 'choices': ['10', '12', '14', '16']},
        ],
        'arithmetic': [
            {'q': '12 + 15 = ?', 'a': '27', 'choices': ['25', '26', '27', '28']},
            {'q': '8 x 7 = ?', 'a': '56', 'choices': ['54', '56', '58', '60']},
            {'q': '100 - 37 = ?', 'a': '63', 'choices': ['61', '62', '63', '64']},
            {'q': '144 / 12 = ?', 'a': '12', 'choices': ['10', '11', '12', '13']},
        ],
        'general': [
            {'q': 'What is 5 squared?', 'a': '25', 'choices': ['20', '25', '30', '35']},
            {'q': 'What is the square root of 49?', 'a': '7', 'choices': ['6', '7', '8', '9']},
            {'q': 'What is 10% of 200?', 'a': '20', 'choices': ['15', '20', '25', '30']},
        ]
    },
    'science': {
        'biology': [
            {'q': 'What is the powerhouse of the cell?', 'a': 'mitochondria', 'choices': ['nucleus', 'mitochondria', 'ribosome', 'vacuole']},
            {'q': 'What process do plants use to make food?', 'a': 'photosynthesis', 'choices': ['respiration', 'photosynthesis', 'digestion', 'fermentation']},
            {'q': 'DNA stands for?', 'a': 'deoxyribonucleic acid', 'choices': ['deoxyribonucleic acid', 'ribonucleic acid', 'amino acid', 'nucleic acid']},
        ],
        'chemistry': [
            {'q': 'What is H2O?', 'a': 'water', 'choices': ['oxygen', 'hydrogen', 'water', 'peroxide']},
            {'q': 'Atomic number of Carbon?', 'a': '6', 'choices': ['4', '6', '8', '12']},
            {'q': 'What is NaCl?', 'a': 'salt', 'choices': ['sugar', 'salt', 'acid', 'base']},
        ],
        'physics': [
            {'q': 'Speed of light is approximately?', 'a': '300000 km/s', 'choices': ['3000 km/s', '30000 km/s', '300000 km/s', '3000000 km/s']},
            {'q': 'Unit of force?', 'a': 'Newton', 'choices': ['Joule', 'Newton', 'Watt', 'Pascal']},
        ],
        'general': [
            {'q': 'Boiling point of water (Celsius)?', 'a': '100', 'choices': ['0', '50', '100', '212']},
            {'q': 'How many planets in our solar system?', 'a': '8', 'choices': ['7', '8', '9', '10']},
        ]
    },
    'english': {
        'grammar': [
            {'q': 'Which is a verb: run, happy, quickly?', 'a': 'run', 'choices': ['run', 'happy', 'quickly', 'none']},
            {'q': 'Plural of "child"?', 'a': 'children', 'choices': ['childs', 'children', 'childrens', 'child']},
            {'q': 'Past tense of "go"?', 'a': 'went', 'choices': ['goed', 'went', 'gone', 'going']},
        ],
        'literature': [
            {'q': 'A story\'s main character is the?', 'a': 'protagonist', 'choices': ['antagonist', 'protagonist', 'narrator', 'author']},
            {'q': 'The turning point in a story is the?', 'a': 'climax', 'choices': ['exposition', 'rising action', 'climax', 'resolution']},
        ],
        'general': [
            {'q': 'How many letters in the alphabet?', 'a': '26', 'choices': ['24', '25', '26', '27']},
            {'q': 'Which is a vowel?', 'a': 'e', 'choices': ['b', 'c', 'e', 'f']},
        ]
    },
    'history': {
        'ancient': [
            {'q': 'Ancient Egypt\'s writing system?', 'a': 'hieroglyphics', 'choices': ['cuneiform', 'hieroglyphics', 'alphabetic', 'pictographic']},
            {'q': 'Roman Empire capital?', 'a': 'Rome', 'choices': ['Athens', 'Rome', 'Alexandria', 'Constantinople']},
        ],
        'modern': [
            {'q': 'World War I began in which year?', 'a': '1914', 'choices': ['1914', '1918', '1939', '1945']},
            {'q': 'The Cold War was between USA and?', 'a': 'USSR', 'choices': ['China', 'USSR', 'Germany', 'Japan']},
        ],
        'general': [
            {'q': 'What year did Columbus sail?', 'a': '1492', 'choices': ['1492', '1500', '1520', '1607']},
            {'q': 'First US President?', 'a': 'George Washington', 'choices': ['Thomas Jefferson', 'George Washington', 'John Adams', 'Benjamin Franklin']},
        ]
    }
}

# Quiz Demo API Endpoints
@app.route('/api/quiz/generate', methods=['POST'])
@login_required
def generate_quiz():
    """Generate a quiz for the student based on class subject"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        num_questions = data.get('num_questions', 5)
        
        if not class_id:
            return jsonify({'success': False, 'error': 'class_id is required'}), 400
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user or user.role != 'student':
            return jsonify({'success': False, 'error': 'Only students can take quizzes'}), 403
        
        class_obj = Class.query.get(class_id)
        if not class_obj or user not in class_obj.users:
            return jsonify({'success': False, 'error': 'Not enrolled in this class'}), 403
        
        subject = (class_obj.subject or 'math').lower()
        subject_aliases = {
            'mathematics': 'math',
            'maths': 'math',
            'sciences': 'science',
            'bio': 'science',
            'lit': 'english',
            'literature': 'english',
            'social studies': 'history'
        }
        subject = subject_aliases.get(subject, subject)
        if subject not in QUESTION_BANK:
            subject = 'math'
        
        subject_questions = QUESTION_BANK[subject]
        all_questions = []
        for topic_questions in subject_questions.values():
            all_questions.extend(topic_questions)
        
        num_questions = min(num_questions, len(all_questions))
        selected_questions = random.sample(all_questions, num_questions)
        
        ai_model = class_obj.ai_model
        if not ai_model:
            ai_model = AIModel.query.first()
        
        if not ai_model:
            return jsonify({'success': False, 'error': 'No AI model available'}), 500
        
        skills_tested = list(subject_questions.keys())
        
        mini_test = MiniTest(
            class_id=class_id,
            created_by_ai=ai_model.id,
            test_type='quiz',
            difficulty_level='medium',
            skills_tested=json.dumps(skills_tested),
            questions=json.dumps(selected_questions)
        )
        db.session.add(mini_test)
        db.session.commit()
        
        questions_for_display = []
        for i, q in enumerate(selected_questions):
            questions_for_display.append({
                'index': i,
                'question': q['q'],
                'choices': q['choices']
            })
        
        return jsonify({
            'success': True,
            'quiz_id': mini_test.id,
            'subject': subject,
            'num_questions': len(selected_questions),
            'questions': questions_for_display
        })
        
    except Exception as e:
        app.logger.error(f'Quiz generation error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    """Submit quiz answers and update mastery"""
    try:
        data = request.get_json()
        quiz_id = data.get('quiz_id')
        answers = data.get('answers', [])
        time_taken = data.get('time_taken')
        
        if not quiz_id:
            return jsonify({'success': False, 'error': 'quiz_id is required'}), 400
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user or user.role != 'student':
            return jsonify({'success': False, 'error': 'Only students can submit quizzes'}), 403
        
        mini_test = MiniTest.query.get(quiz_id)
        if not mini_test:
            return jsonify({'success': False, 'error': 'Quiz not found'}), 404
        
        class_obj = Class.query.get(mini_test.class_id)
        if not class_obj or user not in class_obj.users:
            return jsonify({'success': False, 'error': 'Not enrolled in this class'}), 403
        
        questions = json.loads(mini_test.questions)
        
        correct = 0
        results = []
        for i, question in enumerate(questions):
            student_answer = answers[i] if i < len(answers) else ''
            is_correct = student_answer.lower().strip() == question['a'].lower().strip()
            if is_correct:
                correct += 1
            results.append({
                'question': question['q'],
                'correct_answer': question['a'],
                'student_answer': student_answer,
                'is_correct': is_correct
            })
        
        score = (correct / len(questions)) * 100 if questions else 0
        
        skills_tested = json.loads(mini_test.skills_tested)
        skill_scores = {}
        for skill in skills_tested:
            skill_scores[skill] = score
        
        response = MiniTestResponse(
            test_id=quiz_id,
            user_id=user_id,
            answers=json.dumps(answers),
            score=score,
            time_taken=time_taken,
            skill_scores=json.dumps(skill_scores)
        )
        db.session.add(response)
        
        profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = OptimizedProfile(user_id=user_id)
            db.session.add(profile)
        
        existing_mastery = {}
        if profile.mastery_scores:
            existing_mastery = json.loads(profile.mastery_scores)
        
        for skill, new_score in skill_scores.items():
            if skill in existing_mastery:
                existing_mastery[skill] = existing_mastery[skill] * 0.7 + new_score * 0.3
            else:
                existing_mastery[skill] = new_score
        
        profile.mastery_scores = json.dumps(existing_mastery)
        profile.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'score': score,
            'correct': correct,
            'total': len(questions),
            'results': results,
            'mastery_updated': existing_mastery
        })
        
    except Exception as e:
        app.logger.error(f'Quiz submission error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/student/mastery')
@login_required
def get_student_mastery():
    """Get current mastery levels for student"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user or user.role != 'student':
            return jsonify({'success': False, 'error': 'Only students can view mastery'}), 403
        
        profile = OptimizedProfile.query.filter_by(user_id=user_id).first()
        
        mastery = {}
        if profile and profile.mastery_scores:
            mastery = json.loads(profile.mastery_scores)
        
        quiz_history = MiniTestResponse.query.filter_by(user_id=user_id).order_by(
            MiniTestResponse.completed_at.desc()
        ).limit(10).all()
        
        recent_quizzes = []
        for response in quiz_history:
            test = MiniTest.query.get(response.test_id)
            recent_quizzes.append({
                'quiz_id': response.test_id,
                'score': response.score,
                'completed_at': response.completed_at.isoformat() if response.completed_at else None,
                'test_type': test.test_type if test else 'quiz'
            })
        
        return jsonify({
            'success': True,
            'mastery': mastery,
            'recent_quizzes': recent_quizzes,
            'overall_score': sum(mastery.values()) / len(mastery) if mastery else 0
        })
        
    except Exception as e:
        app.logger.error(f'Mastery fetch error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500