from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import *
from app.utils.decorators import role_required
from app.utils.backup import BackupManager
from werkzeug.utils import secure_filename
import os
import asyncio

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@role_required('admin', 'assistant')
def dashboard():
    stats = {
        'students': Student.query.count(),
        'teachers': Teacher.query.count(),
        'courses': Course.query.count(),
        'enrollments': Enrollment.query.count()
    }
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_contacts=recent_contacts)

@bp.route('/backup', methods=['GET', 'POST'])
@role_required('admin')
def backup():
    if request.method == 'POST':
        backup_type = request.form.get('backup_type')
        send_telegram = request.form.get('send_telegram') == 'on'
        
        try:
            if backup_type == 'full':
                file_path = BackupManager.create_full_backup()
            elif backup_type == 'structure':
                file_path = BackupManager.create_structure_backup()
            elif backup_type == 'data':
                file_path = BackupManager.create_data_backup()
            else:
                flash('نوع النسخة الاحتياطية غير صحيح', 'danger')
                return redirect(url_for('admin.backup'))
            
            if send_telegram and current_app.config['TELEGRAM_BACKUP_ENABLED']:
                asyncio.run(BackupManager.send_to_telegram(file_path))
            
            flash(f'تم إنشاء النسخة الاحتياطية بنجاح: {file_path}', 'success')
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            flash(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}', 'danger')
    
    return render_template('admin/backup.html')

@bp.route('/users')
@role_required('admin')
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@bp.route('/users/add', methods=['GET', 'POST'])
@role_required('admin')
def add_user():
    if request.method == 'POST':
        user = User(
            phone_number=request.form.get('phone_number'),
            full_name=request.form.get('full_name'),
            role=request.form.get('role'),
            is_active=True
        )
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.flush()
        
        if user.role == 'teacher':
            teacher = Teacher(
                user_id=user.id,
                specialization='غير محدد',
                bio='',
                experience_years=0
            )
            db.session.add(teacher)
        elif user.role == 'student':
            student = Student(
                user_id=user.id,
                full_name=user.full_name,
                birth_date=None,
                phone='',
                address=''
            )
            db.session.add(student)
        
        db.session.commit()
        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/add_user.html')

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    old_role = user.role
    
    if request.method == 'POST':
        user.phone_number = request.form.get('phone_number')
        user.full_name = request.form.get('full_name')
        new_role = request.form.get('role')
        user.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        
        if old_role != new_role:
            if old_role == 'teacher':
                Teacher.query.filter_by(user_id=user.id).delete()
            elif old_role == 'student':
                Student.query.filter_by(user_id=user.id).delete()
            
            user.role = new_role
            db.session.flush()
            
            if new_role == 'teacher':
                teacher = Teacher(
                    user_id=user.id,
                    specialization='غير محدد',
                    bio='',
                    experience_years=0
                )
                db.session.add(teacher)
            elif new_role == 'student':
                student = Student(
                    user_id=user.id,
                    full_name=user.full_name,
                    birth_date=None,
                    phone='',
                    address=''
                )
                db.session.add(student)
        
        db.session.commit()
        flash('تم تحديث المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@bp.route('/courses')
@role_required('admin', 'assistant')
def courses():
    all_courses = Course.query.all()
    return render_template('admin/courses.html', courses=all_courses)

@bp.route('/courses/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_course():
    if request.method == 'POST':
        course = Course(
            title=request.form.get('title'),
            description=request.form.get('description'),
            short_description=request.form.get('short_description'),
            duration=request.form.get('duration'),
            level=request.form.get('level'),
            is_featured=request.form.get('is_featured') == 'on'
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                course.image = f'courses/{filename}'
        
        db.session.add(course)
        db.session.commit()
        flash('تم إضافة الدورة بنجاح', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/add_course.html')

@bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.short_description = request.form.get('short_description')
        course.duration = request.form.get('duration')
        course.level = request.form.get('level')
        course.is_featured = request.form.get('is_featured') == 'on'
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                course.image = f'courses/{filename}'
        
        db.session.commit()
        flash('تم تحديث الدورة بنجاح', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/edit_course.html', course=course)

@bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@role_required('admin', 'assistant')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('تم حذف الدورة بنجاح', 'success')
    return redirect(url_for('admin.courses'))

@bp.route('/settings', methods=['GET', 'POST'])
@role_required('admin')
def settings():
    site_settings = SiteSettings.query.first()
    if not site_settings:
        site_settings = SiteSettings()
        db.session.add(site_settings)
        db.session.commit()
    
    if request.method == 'POST':
        site_settings.institute_name = request.form.get('institute_name')
        site_settings.about_title = request.form.get('about_title')
        site_settings.about_content = request.form.get('about_content')
        site_settings.founding_date = request.form.get('founding_date')
        site_settings.mission_statement = request.form.get('mission_statement')
        site_settings.facebook_url = request.form.get('facebook_url')
        site_settings.phone1 = request.form.get('phone1')
        site_settings.phone2 = request.form.get('phone2')
        site_settings.email = request.form.get('email')
        site_settings.address = request.form.get('address')
        db.session.commit()
        flash('تم تحديث الإعدادات بنجاح', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=site_settings)

@bp.route('/news')
@role_required('admin', 'assistant')
def news():
    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news.html', news=all_news)

@bp.route('/news/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_news():
    if request.method == 'POST':
        news = News(
            title=request.form.get('title'),
            content=request.form.get('content'),
            author_id=current_user.id,
            is_published=request.form.get('is_published') == 'on'
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'news', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                news.image = f'news/{filename}'
        
        db.session.add(news)
        db.session.commit()
        flash('تم إضافة الخبر بنجاح', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/add_news.html')

@bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        news.title = request.form.get('title')
        news.content = request.form.get('content')
        news.is_published = request.form.get('is_published') == 'on'
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'news', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                news.image = f'news/{filename}'
        
        db.session.commit()
        flash('تم تحديث الخبر بنجاح', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/edit_news.html', news=news)

@bp.route('/news/delete/<int:news_id>', methods=['POST'])
@role_required('admin', 'assistant')
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('تم حذف الخبر بنجاح', 'success')
    return redirect(url_for('admin.news'))
