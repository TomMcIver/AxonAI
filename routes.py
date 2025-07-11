from flask import render_template, request, redirect, url_for, flash, session, send_file
from app import app, db
from models import User, Class, Assignment, AssignmentSubmission, Grade, ContentFile
from auth import hash_password, check_password, login_required, admin_required, get_current_user, role_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime

@app.route('/')
def index():
    """Serve the React frontend"""
    return render_template('spa_loader.html')

@app.route('/legacy-login', methods=['GET', 'POST'])
def login():
    """Login page with user type selection"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if not all([email, password, user_type]):
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')
        
        # Find user by email and role
        user = User.query.filter_by(email=email, role=user_type, is_active=True).first()
        
        if user and check_password(password, user.password_hash):
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.get_full_name()
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials or user type.', 'danger')
    
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
        # Get teacher's classes
        teacher_classes = Class.query.filter_by(teacher_id=user.id, is_active=True).all()
        total_students = sum(cls.get_student_count() for cls in teacher_classes)
        
        return render_template('teacher_dashboard.html', 
                             user=user,
                             classes=teacher_classes,
                             total_students=total_students)
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
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if not all([email, password, role, first_name, last_name]):
            flash('Please fill in all fields.', 'danger')
            return render_template('edit_user.html', user=None, roles=['admin', 'teacher', 'student'])
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('A user with this email already exists.', 'danger')
            return render_template('edit_user.html', user=None, roles=['admin', 'teacher', 'student'])
        
        # Create new user
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        
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
        email = request.form.get('email')
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        
        if not all([email, role, first_name, last_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('edit_user.html', user=user, roles=['admin', 'teacher', 'student'])
        
        # Check if email is taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('A user with this email already exists.', 'danger')
            return render_template('edit_user.html', user=user, roles=['admin', 'teacher', 'student'])
        
        # Update user
        user.email = email
        user.role = role
        user.first_name = first_name
        user.last_name = last_name
        
        # Update password if provided
        if password:
            user.password_hash = hash_password(password)
        
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
    
    assignments = Assignment.query.filter_by(class_id=class_id, is_active=True).all()
    
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
                'email': student.email,
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
        profile = {
            'student': student,
            'ai_profile': student.get_ai_profile_summary(),
            'chat_count': ChatMessage.query.filter_by(user_id=student.id, class_id=class_id).count(),
            'recent_topics': [chat.message[:50] for chat in ChatMessage.query.filter_by(
                user_id=student.id, class_id=class_id
            ).order_by(ChatMessage.created_at.desc()).limit(3).all()]
        }
        student_profiles.append(profile)
    
    return render_template('teacher_ai_insights.html',
                         class_obj=class_obj,
                         insights=insights,
                         student_profiles=student_profiles)
