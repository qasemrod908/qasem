from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('حسابك غير نشط. يرجى التواصل مع الإدارة', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            if user.role == 'admin' or user.role == 'assistant':
                return redirect(next_page or url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(next_page or url_for('teacher.dashboard'))
            elif user.role == 'student':
                return redirect(next_page or url_for('student.dashboard'))
            else:
                return redirect(next_page or url_for('public.index'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('public.index'))
