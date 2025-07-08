from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import User
from auth import hash_password, check_password, login_required, admin_required, get_current_user

@app.route('/')
def index():
    """Redirect to login if not authenticated, otherwise to dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
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
        return render_template('admin_dashboard.html', user=user)
    elif user.role == 'teacher':
        return render_template('teacher_dashboard.html', user=user)
    elif user.role == 'student':
        return render_template('student_dashboard.html', user=user)
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
