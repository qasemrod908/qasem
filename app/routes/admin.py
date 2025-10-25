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
    
    notification_stats = {
        'total': Notification.query.count(),
        'active': Notification.query.filter_by(is_active=True).count(),
        'total_unread': NotificationRecipient.query.filter_by(is_read=False).count()
    }
    
    payment_stats = {
        'total_payments': Payment.query.count(),
        'paid_count': Payment.query.filter_by(status='paid').count(),
        'pending_count': Payment.query.filter_by(status='pending').count() + Payment.query.filter_by(status='partial').count(),
        'total_collected': sum(p.paid_amount for p in Payment.query.all()),
        'total_expected': sum(p.total_amount for p in Payment.query.all())
    }
    payment_stats['total_remaining'] = payment_stats['total_expected'] - payment_stats['total_collected']
    
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          stats=stats, 
                          notification_stats=notification_stats,
                          payment_stats=payment_stats,
                          recent_contacts=recent_contacts,
                          recent_notifications=recent_notifications)

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
            
            site_settings = SiteSettings.query.first()
            if send_telegram and site_settings and site_settings.telegram_backup_enabled:
                import threading
                def send_backup_async():
                    import asyncio
                    asyncio.run(BackupManager.send_to_telegram(
                        file_path, 
                        site_settings.telegram_bot_token, 
                        site_settings.telegram_chat_id
                    ))
                thread = threading.Thread(target=send_backup_async)
                thread.start()
            
            flash(f'تم إنشاء النسخة الاحتياطية بنجاح', 'success')
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            flash(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}', 'danger')
    
    backups = BackupManager.list_backups()
    return render_template('admin/backup.html', backups=backups)

@bp.route('/backup/download/<path:filename>')
@role_required('admin')
def download_backup(filename):
    try:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join('backups', safe_filename)
        
        abs_file_path = os.path.abspath(file_path)
        abs_backups_dir = os.path.abspath('backups')
        
        if not abs_file_path.startswith(abs_backups_dir + os.sep):
            flash('محاولة وصول غير مصرح بها', 'danger')
            return redirect(url_for('admin.backup'))
        
        if not os.path.exists(abs_file_path):
            flash(f'الملف غير موجود: {safe_filename}', 'danger')
            return redirect(url_for('admin.backup'))
        
        if not os.path.isfile(abs_file_path):
            flash('المسار المطلوب ليس ملفاً', 'danger')
            return redirect(url_for('admin.backup'))
        
        return send_file(abs_file_path, as_attachment=True, download_name=safe_filename)
    except Exception as e:
        flash(f'حدث خطأ أثناء تحميل الملف: {str(e)}', 'danger')
        return redirect(url_for('admin.backup'))

@bp.route('/backup/restore', methods=['POST'])
@role_required('admin')
def restore_backup():
    restore_type = request.form.get('restore_type')
    
    if 'backup_file' not in request.files:
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(url_for('admin.backup'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(url_for('admin.backup'))
    
    try:
        filename = secure_filename(file.filename)
        temp_path = os.path.join('temp_uploads', filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(temp_path)
        
        if restore_type == 'full':
            BackupManager.restore_full_backup(temp_path)
            flash('تم استعادة النسخة الاحتياطية الكاملة بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        elif restore_type == 'structure':
            BackupManager.restore_structure_backup(temp_path)
            flash('تم استعادة البنية بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        elif restore_type == 'data':
            BackupManager.restore_data_backup(temp_path)
            flash('تم استعادة البيانات بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        else:
            flash('نوع الاستعادة غير صحيح', 'danger')
            return redirect(url_for('admin.backup'))
        
        os.remove(temp_path)
        
    except Exception as e:
        flash(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup'))

@bp.route('/backup/delete/<path:filename>', methods=['POST'])
@role_required('admin')
def delete_backup(filename):
    try:
        safe_filename = os.path.basename(filename)
        BackupManager.delete_backup(safe_filename)
        flash(f'تم حذف النسخة الاحتياطية "{safe_filename}" بنجاح', 'success')
    except Exception as e:
        flash(f'حدث خطأ أثناء حذف النسخة الاحتياطية: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup'))

@bp.route('/backup/confirm-restore/<path:filename>')
@role_required('admin')
def confirm_restore_backup(filename):
    try:
        safe_filename = os.path.basename(filename)
        backups = BackupManager.list_backups()
        
        backup_info = None
        for backup in backups:
            if backup['name'] == safe_filename:
                backup_info = backup
                break
        
        if not backup_info:
            flash('النسخة الاحتياطية غير موجودة', 'danger')
            return redirect(url_for('admin.backup'))
        
        return render_template('admin/confirm_restore.html', backup=backup_info)
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('admin.backup'))

@bp.route('/backup/restore-existing', methods=['POST'])
@role_required('admin')
def restore_existing_backup():
    filename = request.form.get('filename')
    
    if not filename:
        flash('لم يتم تحديد ملف النسخة الاحتياطية', 'danger')
        return redirect(url_for('admin.backup'))
    
    try:
        from werkzeug.security import safe_join
        
        safe_filename = os.path.basename(filename)
        backups_dir = os.path.abspath('backups')
        file_path = safe_join(backups_dir, safe_filename)
        
        if file_path is None:
            flash('محاولة وصول غير مصرح بها', 'danger')
            return redirect(url_for('admin.backup'))
        
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(backups_dir + os.sep):
            flash('محاولة وصول غير مصرح بها', 'danger')
            return redirect(url_for('admin.backup'))
        
        if not os.path.exists(file_path):
            flash('الملف غير موجود', 'danger')
            return redirect(url_for('admin.backup'))
        
        if safe_filename.startswith('full_') and safe_filename.endswith('.zip'):
            BackupManager.restore_full_backup(file_path)
            flash('تم استعادة النسخة الاحتياطية الكاملة بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        elif safe_filename.startswith('structure_') and safe_filename.endswith('.zip'):
            BackupManager.restore_structure_backup(file_path)
            flash('تم استعادة البنية بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        elif safe_filename.startswith('data_') and safe_filename.endswith('.db'):
            BackupManager.restore_data_backup(file_path)
            flash('تم استعادة البيانات بنجاح. سيتم إعادة تشغيل التطبيق.', 'success')
        else:
            flash('نوع النسخة الاحتياطية غير معروف أو غير مدعوم', 'danger')
            return redirect(url_for('admin.backup'))
        
    except Exception as e:
        flash(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}', 'danger')
    
    return redirect(url_for('admin.backup'))

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
                student_number='',
                phone='',
                address='',
                date_of_birth=None
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
                    student_number='',
                    phone='',
                    address='',
                    date_of_birth=None
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
        from datetime import datetime as dt
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        max_students = request.form.get('max_students')
        
        course = Course(
            title=request.form.get('title'),
            description=request.form.get('description'),
            short_description=request.form.get('short_description'),
            duration=request.form.get('duration'),
            level=request.form.get('level'),
            is_featured=request.form.get('is_featured') == 'on',
            start_date=dt.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=dt.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            max_students=int(max_students) if max_students else None
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
        from datetime import datetime as dt
        
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.short_description = request.form.get('short_description')
        course.duration = request.form.get('duration')
        course.level = request.form.get('level')
        course.is_featured = request.form.get('is_featured') == 'on'
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        max_students = request.form.get('max_students')
        
        course.start_date = dt.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        course.end_date = dt.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        course.max_students = int(max_students) if max_students else None
        
        if request.form.get('delete_image') == 'on':
            if course.image:
                try:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], course.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except:
                    pass
                course.image = None
        
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
        site_settings.telegram_bot_token = request.form.get('telegram_bot_token')
        site_settings.telegram_chat_id = request.form.get('telegram_chat_id')
        site_settings.telegram_backup_enabled = request.form.get('telegram_backup_enabled') == 'on'
        
        site_settings.courses_slider_items = int(request.form.get('courses_slider_items', 3))
        site_settings.courses_slider_interval = int(request.form.get('courses_slider_interval', 5000))
        site_settings.courses_slider_auto_play = request.form.get('courses_slider_auto_play') == 'on'
        site_settings.courses_slider_transition = request.form.get('courses_slider_transition', 'slide')
        
        site_settings.teachers_slider_items = int(request.form.get('teachers_slider_items', 4))
        site_settings.teachers_slider_interval = int(request.form.get('teachers_slider_interval', 5000))
        site_settings.teachers_slider_auto_play = request.form.get('teachers_slider_auto_play') == 'on'
        site_settings.teachers_slider_transition = request.form.get('teachers_slider_transition', 'slide')
        
        db.session.commit()
        flash('تم تحديث الإعدادات بنجاح', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=site_settings)

@bp.route('/bot', methods=['GET', 'POST'])
@role_required('admin')
def bot_management():
    site_settings = SiteSettings.query.first()
    if not site_settings:
        site_settings = SiteSettings()
        db.session.add(site_settings)
        db.session.commit()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_settings':
            site_settings.telegram_bot_enabled = request.form.get('telegram_bot_enabled') == 'on'
            site_settings.telegram_bot_notifications_enabled = request.form.get('telegram_bot_notifications_enabled') == 'on'
            site_settings.telegram_bot_webhook_enabled = request.form.get('telegram_bot_webhook_enabled') == 'on'
            site_settings.telegram_bot_webhook_url = request.form.get('telegram_bot_webhook_url')
            
            db.session.commit()
            flash('تم تحديث إعدادات البوت بنجاح', 'success')
        
        return redirect(url_for('admin.bot_management'))
    
    bot_stats = BotStatistics.query.order_by(BotStatistics.date.desc()).first()
    total_bot_users = BotSession.query.count()
    authenticated_users = BotSession.query.filter_by(is_authenticated=True).count()
    
    recent_sessions = BotSession.query.order_by(BotSession.last_activity.desc()).limit(10).all()
    
    stats = {
        'total_users': total_bot_users,
        'authenticated_users': authenticated_users,
        'active_users_today': bot_stats.active_users_today if bot_stats else 0,
        'messages_sent': bot_stats.messages_sent if bot_stats else 0,
        'messages_received': bot_stats.messages_received if bot_stats else 0
    }
    
    return render_template('admin/bot.html', 
                         settings=site_settings, 
                         stats=stats,
                         recent_sessions=recent_sessions)

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

@bp.route('/teachers')
@role_required('admin', 'assistant')
def teachers():
    all_teachers = Teacher.query.all()
    return render_template('admin/teachers.html', teachers=all_teachers)

@bp.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if request.method == 'POST':
        teacher.specialization = request.form.get('specialization')
        teacher.bio = request.form.get('bio')
        teacher.experience_years = request.form.get('experience_years')
        teacher.qualifications = request.form.get('qualifications')
        teacher.phone = request.form.get('phone')
        
        if request.form.get('delete_photo') == 'on':
            if teacher.photo:
                try:
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], teacher.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except:
                    pass
                teacher.photo = None
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'teachers', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                teacher.photo = f'teachers/{filename}'
        
        db.session.commit()
        flash('تم تحديث بيانات المدرس بنجاح', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/edit_teacher.html', teacher=teacher)

@bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'تفعيل' if user.is_active else 'تعطيل'
    flash(f'تم {status} المستخدم بنجاح', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    if user_id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'teacher':
        Teacher.query.filter_by(user_id=user.id).delete()
    elif user.role == 'student':
        Student.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/students')
@role_required('admin', 'assistant')
def students():
    all_students = Student.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('admin/students.html', students=all_students, teachers=teachers, courses=courses)

@bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.student_number = request.form.get('student_number')
        student.phone = request.form.get('phone')
        student.address = request.form.get('address')
        student.guardian_name = request.form.get('guardian_name')
        student.guardian_phone = request.form.get('guardian_phone')
        
        class_grade_id = request.form.get('class_grade_id')
        section_id = request.form.get('section_id')
        
        if section_id and class_grade_id:
            section = Section.query.get(int(section_id))
            if section and section.class_grade_id != int(class_grade_id):
                flash('الشعبة المختارة لا تنتمي للصف المحدد', 'danger')
                grades = ClassGrade.query.order_by(ClassGrade.display_order, ClassGrade.name).all()
                sections = Section.query.order_by(Section.display_order, Section.name).all()
                return render_template('admin/edit_student.html', student=student, grades=grades, sections=sections)
        
        student.class_grade_id = int(class_grade_id) if class_grade_id else None
        student.section_id = int(section_id) if section_id else None
        
        dob = request.form.get('date_of_birth')
        if dob:
            from datetime import datetime
            student.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        
        if request.form.get('delete_photo') == 'on':
            if student.photo:
                try:
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], student.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except:
                    pass
                student.photo = None
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'students', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                student.photo = f'students/{filename}'
        
        db.session.commit()
        flash('تم تحديث بيانات الطالب بنجاح', 'success')
        return redirect(url_for('admin.students'))
    
    grades = ClassGrade.query.order_by(ClassGrade.display_order, ClassGrade.name).all()
    sections = Section.query.order_by(Section.display_order, Section.name).all()
    return render_template('admin/edit_student.html', student=student, grades=grades, sections=sections)

@bp.route('/students/view/<int:student_id>')
@role_required('admin', 'assistant')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    enrollments = student.enrollments.all()
    grades = Grade.query.filter_by(student_id=student_id).order_by(Grade.created_at.desc()).all()
    attendance_records = Attendance.query.filter_by(user_id=student.user_id).order_by(Attendance.date.desc()).limit(10).all()
    stats = Attendance.get_user_stats(student.user_id)
    return render_template('admin/view_student.html', student=student, enrollments=enrollments, grades=grades, 
                         attendance_records=attendance_records, stats=stats)

@bp.route('/students/<int:student_id>/grades/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_student_grade(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        from datetime import datetime
        
        exam_date_str = request.form.get('exam_date')
        exam_date_obj = None
        if exam_date_str:
            try:
                exam_date_obj = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        grade = Grade(
            student_id=student_id,
            course_id=request.form.get('course_id'),
            teacher_id=request.form.get('teacher_id'),
            exam_name=request.form.get('exam_name'),
            grade=request.form.get('grade'),
            max_grade=request.form.get('max_grade'),
            notes=request.form.get('notes'),
            exam_date=exam_date_obj
        )
        
        db.session.add(grade)
        db.session.commit()
        
        from app.utils.notifications import send_new_grade_notification
        send_new_grade_notification(grade.id)
        
        flash('تم إضافة العلامة بنجاح', 'success')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    courses = Course.query.all()
    teachers = Teacher.query.all()
    return render_template('admin/add_student_grade.html', student=student, courses=courses, teachers=teachers)

@bp.route('/students/<int:student_id>/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_student_grade(student_id, grade_id):
    student = Student.query.get_or_404(student_id)
    grade = Grade.query.get_or_404(grade_id)
    
    if grade.student_id != student_id:
        flash('هذه العلامة لا تنتمي لهذا الطالب', 'danger')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    if request.method == 'POST':
        from datetime import datetime
        
        exam_date_str = request.form.get('exam_date')
        exam_date_obj = None
        if exam_date_str:
            try:
                exam_date_obj = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        grade.course_id = request.form.get('course_id')
        grade.teacher_id = request.form.get('teacher_id')
        grade.exam_name = request.form.get('exam_name')
        grade.grade = request.form.get('grade')
        grade.max_grade = request.form.get('max_grade')
        grade.notes = request.form.get('notes')
        grade.exam_date = exam_date_obj
        
        db.session.commit()
        
        from app.utils.notifications import send_updated_grade_notification
        send_updated_grade_notification(grade.id)
        
        flash('تم تحديث العلامة بنجاح', 'success')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    courses = Course.query.all()
    teachers = Teacher.query.all()
    return render_template('admin/edit_student_grade.html', student=student, grade=grade, courses=courses, teachers=teachers)

@bp.route('/students/<int:student_id>/grades/delete/<int:grade_id>', methods=['POST'])
@role_required('admin')
def delete_student_grade(student_id, grade_id):
    grade = Grade.query.get_or_404(grade_id)
    
    if grade.student_id != student_id:
        flash('هذه العلامة لا تنتمي لهذا الطالب', 'danger')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    db.session.delete(grade)
    db.session.commit()
    flash('تم حذف العلامة بنجاح', 'success')
    return redirect(url_for('admin.view_student', student_id=student_id))

@bp.route('/students/delete/<int:student_id>', methods=['POST'])
@role_required('admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    db.session.delete(student)
    if user:
        db.session.delete(user)
    
    db.session.commit()
    flash('تم حذف الطالب بنجاح', 'success')
    return redirect(url_for('admin.students'))

@bp.route('/students/enroll/<int:student_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def enroll_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        teacher_id = request.form.get('teacher_id')
        
        if not course_id:
            flash('يجب اختيار دورة', 'danger')
            teachers = Teacher.query.all()
            courses = Course.query.all()
            return render_template('admin/enroll_student.html', student=student, teachers=teachers, courses=courses)
        
        course = Course.query.get_or_404(course_id)
        
        existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if existing:
            flash('الطالب مسجل بالفعل في هذه الدورة', 'warning')
            return redirect(url_for('admin.students'))
        
        if course.max_students:
            available = course.available_seats()
            if available is not None and available <= 0:
                flash(f'عذراً، الدورة "{course.title}" مكتملة ولا يوجد مقاعد متاحة', 'danger')
                return redirect(url_for('admin.students'))
        
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            teacher_id=teacher_id if teacher_id else None
        )
        db.session.add(enrollment)
        db.session.commit()
        flash(f'تم تسجيل الطالب في دورة "{course.title}" بنجاح', 'success')
        return redirect(url_for('admin.students'))
    
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('admin/enroll_student.html', student=student, teachers=teachers, courses=courses)

@bp.route('/students/unenroll/<int:enrollment_id>', methods=['POST'])
@role_required('admin', 'assistant')
def unenroll_student(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('تم إلغاء تسجيل الطالب من الدورة بنجاح', 'success')
    return redirect(url_for('admin.students'))

@bp.route('/grades')
@role_required('admin', 'assistant')
def grades():
    all_grades = ClassGrade.query.order_by(ClassGrade.display_order, ClassGrade.name).all()
    return render_template('admin/grades.html', grades=all_grades)

@bp.route('/grades/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_grade():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        display_order = request.form.get('display_order', 0)
        
        existing = ClassGrade.query.filter_by(name=name).first()
        if existing:
            flash('الصف موجود بالفعل', 'warning')
            return redirect(url_for('admin.grades'))
        
        grade = ClassGrade(
            name=name,
            description=description,
            display_order=int(display_order) if display_order else 0
        )
        db.session.add(grade)
        db.session.commit()
        flash('تم إضافة الصف بنجاح', 'success')
        return redirect(url_for('admin.grades'))
    
    return render_template('admin/add_grade.html')

@bp.route('/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_grade(grade_id):
    grade = ClassGrade.query.get_or_404(grade_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        display_order = request.form.get('display_order', 0)
        
        existing = ClassGrade.query.filter(ClassGrade.name == name, ClassGrade.id != grade_id).first()
        if existing:
            flash('اسم الصف موجود بالفعل', 'warning')
            return redirect(url_for('admin.edit_grade', grade_id=grade_id))
        
        grade.name = name
        grade.description = description
        grade.display_order = int(display_order) if display_order else 0
        
        db.session.commit()
        flash('تم تحديث الصف بنجاح', 'success')
        return redirect(url_for('admin.grades'))
    
    return render_template('admin/edit_grade.html', grade=grade)

@bp.route('/grades/delete/<int:grade_id>', methods=['POST'])
@role_required('admin')
def delete_grade(grade_id):
    grade = ClassGrade.query.get_or_404(grade_id)
    
    if grade.students.count() > 0:
        flash('لا يمكن حذف الصف لأنه يحتوي على طلاب', 'danger')
        return redirect(url_for('admin.grades'))
    
    db.session.delete(grade)
    db.session.commit()
    flash('تم حذف الصف بنجاح', 'success')
    return redirect(url_for('admin.grades'))

@bp.route('/grades/<int:grade_id>/sections/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_section(grade_id):
    grade = ClassGrade.query.get_or_404(grade_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        max_students = request.form.get('max_students')
        display_order = request.form.get('display_order', 0)
        
        existing = Section.query.filter_by(name=name, class_grade_id=grade_id).first()
        if existing:
            flash('الشعبة موجودة بالفعل في هذا الصف', 'warning')
            return render_template('admin/add_section.html', grade=grade)
        
        section = Section(
            name=name,
            class_grade_id=grade_id,
            description=description,
            max_students=int(max_students) if max_students else None,
            display_order=int(display_order) if display_order else 0
        )
        db.session.add(section)
        db.session.commit()
        flash('تم إضافة الشعبة بنجاح', 'success')
        return redirect(url_for('admin.grades'))
    
    return render_template('admin/add_section.html', grade=grade)

@bp.route('/sections/edit/<int:section_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        max_students = request.form.get('max_students')
        display_order = request.form.get('display_order', 0)
        
        existing = Section.query.filter(
            Section.name == name,
            Section.class_grade_id == section.class_grade_id,
            Section.id != section_id
        ).first()
        if existing:
            flash('اسم الشعبة موجود بالفعل في هذا الصف', 'warning')
            return redirect(url_for('admin.edit_section', section_id=section_id))
        
        section.name = name
        section.description = description
        section.max_students = int(max_students) if max_students else None
        section.display_order = int(display_order) if display_order else 0
        
        db.session.commit()
        flash('تم تحديث الشعبة بنجاح', 'success')
        return redirect(url_for('admin.grades'))
    
    return render_template('admin/edit_section.html', section=section)

@bp.route('/sections/delete/<int:section_id>', methods=['POST'])
@role_required('admin')
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    
    if section.students.count() > 0:
        flash('لا يمكن حذف الشعبة لأنها تحتوي على طلاب', 'danger')
        return redirect(url_for('admin.grades'))
    
    db.session.delete(section)
    db.session.commit()
    flash('تم حذف الشعبة بنجاح', 'success')
    return redirect(url_for('admin.grades'))

@bp.route('/lessons')
@role_required('admin', 'assistant')
def lessons():
    all_lessons = Lesson.query.order_by(Lesson.upload_date.desc()).all()
    return render_template('admin/lessons.html', lessons=all_lessons)

@bp.route('/lessons/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_lesson():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        teacher_id = request.form.get('teacher_id')
        title = request.form.get('title')
        description = request.form.get('description')
        
        lesson = Lesson(
            course_id=course_id,
            teacher_id=teacher_id,
            title=title,
            description=description,
            is_published=request.form.get('is_published') == 'on'
        )
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                lesson.file_path = f'uploads/documents/{filename}'
                lesson.file_type = filename.rsplit('.', 1)[1].lower()
        
        db.session.add(lesson)
        db.session.commit()
        flash('تم إضافة الدرس بنجاح', 'success')
        return redirect(url_for('admin.lessons'))
    
    courses = Course.query.all()
    teachers = Teacher.query.all()
    return render_template('admin/add_lesson.html', courses=courses, teachers=teachers)

@bp.route('/lessons/edit/<int:lesson_id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if request.method == 'POST':
        lesson.course_id = request.form.get('course_id')
        lesson.teacher_id = request.form.get('teacher_id')
        lesson.title = request.form.get('title')
        lesson.description = request.form.get('description')
        lesson.is_published = request.form.get('is_published') == 'on'
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                lesson.file_path = f'uploads/documents/{filename}'
                lesson.file_type = filename.rsplit('.', 1)[1].lower()
        
        db.session.commit()
        flash('تم تحديث الدرس بنجاح', 'success')
        return redirect(url_for('admin.lessons'))
    
    courses = Course.query.all()
    teachers = Teacher.query.all()
    return render_template('admin/edit_lesson.html', lesson=lesson, courses=courses, teachers=teachers)

@bp.route('/lessons/delete/<int:lesson_id>', methods=['POST'])
@role_required('admin', 'assistant')
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    db.session.delete(lesson)
    db.session.commit()
    flash('تم حذف الدرس بنجاح', 'success')
    return redirect(url_for('admin.lessons'))

@bp.route('/contacts')
@role_required('admin', 'assistant')
def contacts():
    all_contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin/contacts.html', contacts=all_contacts)

@bp.route('/contacts/view/<int:contact_id>')
@role_required('admin', 'assistant')
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if not contact.is_read:
        contact.is_read = True
        db.session.commit()
    return render_template('admin/view_contact.html', contact=contact)

@bp.route('/contacts/toggle/<int:contact_id>', methods=['POST'])
@role_required('admin', 'assistant')
def toggle_contact_status(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.is_read = not contact.is_read
    db.session.commit()
    status = 'مقروءة' if contact.is_read else 'غير مقروءة'
    flash(f'تم تغيير حالة الرسالة إلى {status}', 'success')
    return redirect(url_for('admin.contacts'))

@bp.route('/contacts/delete/<int:contact_id>', methods=['POST'])
@role_required('admin')
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('تم حذف الرسالة بنجاح', 'success')
    return redirect(url_for('admin.contacts'))

@bp.route('/lessons/view/<int:course_id>')
@role_required('admin', 'assistant')
def view_course_lessons(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    return render_template('admin/view_lessons.html', course=course, lessons=lessons)

@bp.route('/lesson/download/<int:lesson_id>')
@role_required('admin', 'assistant')
def download_lesson(lesson_id):
    from flask import send_file
    import os
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.file_path:
        file_full_path = os.path.join(current_app.root_path, 'static', lesson.file_path)
        if os.path.exists(file_full_path):
            return send_file(file_full_path, as_attachment=True, download_name=os.path.basename(lesson.file_path))
        else:
            flash('الملف غير موجود', 'danger')
    else:
        flash('لا يوجد ملف مرفق لهذا الدرس', 'warning')
    
    return redirect(url_for('admin.lessons'))

@bp.route('/notifications')
@role_required('admin', 'assistant')
def notifications():
    notification_type = request.args.get('notification_type', 'all')
    target_type = request.args.get('target_type', 'all')
    status = request.args.get('status', 'all')
    read_status = request.args.get('read_status', 'all')
    delivery_status = request.args.get('delivery_status', 'all')
    
    query = Notification.query
    
    if notification_type != 'all':
        if notification_type == 'manual':
            query = query.filter(Notification.notification_type == 'general')
        elif notification_type == 'automatic':
            query = query.filter(Notification.notification_type.in_(['new_lesson', 'new_grade', 'updated_grade', 'new_payment', 'payment_received', 'payment_reminder']))
        else:
            query = query.filter(Notification.notification_type == notification_type)
    
    if target_type != 'all':
        if target_type == 'individual':
            query = query.filter(Notification.target_type.in_(['student', 'teacher', 'user']))
        elif target_type == 'group':
            query = query.filter(Notification.target_type.in_(['all', 'all_students', 'all_teachers', 'course']))
        else:
            query = query.filter(Notification.target_type == target_type)
    
    if status != 'all':
        if status == 'active':
            query = query.filter(Notification.is_active == True)
        elif status == 'inactive':
            query = query.filter(Notification.is_active == False)
    
    all_notifications = query.order_by(Notification.created_at.desc()).all()
    
    if read_status != 'all' or delivery_status != 'all':
        filtered_notifications = []
        for notif in all_notifications:
            stats = notif.get_delivery_stats()
            include = True
            
            if read_status == 'read' and stats['read'] == 0:
                include = False
            elif read_status == 'unread' and stats['unread'] == 0:
                include = False
            
            if delivery_status == 'telegram' and stats['delivered_telegram'] == 0:
                include = False
            elif delivery_status == 'web' and stats['delivered_web'] == 0:
                include = False
            
            if include:
                filtered_notifications.append(notif)
        
        all_notifications = filtered_notifications
    
    filters = {
        'notification_type': notification_type,
        'target_type': target_type,
        'status': status,
        'read_status': read_status,
        'delivery_status': delivery_status
    }
    
    return render_template('admin/notifications.html', 
                          notifications=all_notifications,
                          filters=filters)

@bp.route('/notifications/create', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def create_notification():
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('notification_type', 'general')
        target_type = request.form.get('target_type', 'all')
        target_id = request.form.get('target_id')
        send_telegram = request.form.get('send_telegram') == 'on'
        send_web = request.form.get('send_web') == 'on'
        
        if not title or not message:
            flash('يرجى إدخال العنوان والرسالة', 'danger')
            return redirect(url_for('admin.create_notification'))
        
        try:
            from app.utils.notifications import create_notification
            
            notification = create_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                created_by_id=current_user.id,
                target_type=target_type,
                target_id=int(target_id) if target_id else None,
                send_telegram=send_telegram,
                send_web=send_web
            )
            
            flash(f'تم إرسال الإشعار بنجاح إلى {len(notification.recipients)} مستخدم', 'success')
            return redirect(url_for('admin.notifications'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    students = Student.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('admin/create_notification.html', 
                          students=students, 
                          teachers=teachers, 
                          courses=courses)

@bp.route('/notifications/view/<int:notification_id>')
@role_required('admin', 'assistant')
def view_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    stats = notification.get_delivery_stats()
    return render_template('admin/view_notification.html', 
                          notification=notification, 
                          stats=stats)

@bp.route('/notifications/toggle/<int:notification_id>', methods=['POST'])
@role_required('admin', 'assistant')
def toggle_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_active = not notification.is_active
    db.session.commit()
    status = 'تم تفعيل الإشعار بنجاح' if notification.is_active else 'تم تعطيل الإشعار بنجاح'
    flash(status, 'success')
    return redirect(url_for('admin.notifications'))

@bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@role_required('admin')
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    flash('تم حذف الإشعار بنجاح', 'success')
    return redirect(url_for('admin.notifications'))

@bp.route('/notifications/bulk-action', methods=['POST'])
@role_required('admin')
def bulk_notification_action():
    action = request.form.get('action')
    notification_ids = request.form.getlist('notification_ids[]')
    
    if not notification_ids:
        flash('يرجى تحديد إشعار واحد على الأقل', 'warning')
        return redirect(url_for('admin.notifications'))
    
    notification_ids = [int(nid) for nid in notification_ids]
    notifications = Notification.query.filter(Notification.id.in_(notification_ids)).all()
    
    if action == 'delete':
        count = len(notifications)
        for notif in notifications:
            db.session.delete(notif)
        db.session.commit()
        flash(f'تم حذف {count} إشعار بنجاح', 'success')
    
    elif action == 'activate':
        count = 0
        for notif in notifications:
            if not notif.is_active:
                notif.is_active = True
                count += 1
        db.session.commit()
        flash(f'تم تفعيل {count} إشعار', 'success')
    
    elif action == 'deactivate':
        count = 0
        for notif in notifications:
            if notif.is_active:
                notif.is_active = False
                count += 1
        db.session.commit()
        flash(f'تم تعطيل {count} إشعار', 'success')
    
    return redirect(url_for('admin.notifications'))

@bp.route('/notifications/stats')
@role_required('admin', 'assistant')
def notifications_stats():
    total_notifications = Notification.query.count()
    active_notifications = Notification.query.filter_by(is_active=True).count()
    total_recipients = NotificationRecipient.query.count()
    total_read = NotificationRecipient.query.filter_by(is_read=True).count()
    total_unread = NotificationRecipient.query.filter_by(is_read=False).count()
    telegram_delivered = NotificationRecipient.query.filter_by(telegram_delivered=True).count()
    web_delivered = NotificationRecipient.query.filter_by(web_delivered=True).count()
    
    stats = {
        'total_notifications': total_notifications,
        'active_notifications': active_notifications,
        'total_recipients': total_recipients,
        'total_read': total_read,
        'total_unread': total_unread,
        'telegram_delivered': telegram_delivered,
        'web_delivered': web_delivered,
        'read_rate': (total_read / total_recipients * 100) if total_recipients > 0 else 0,
        'telegram_delivery_rate': (telegram_delivered / total_recipients * 100) if total_recipients > 0 else 0,
        'web_delivery_rate': (web_delivered / total_recipients * 100) if total_recipients > 0 else 0
    }
    
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
    
    return render_template('admin/notifications_stats.html', 
                          stats=stats, 
                          recent_notifications=recent_notifications)

@bp.route('/students/<int:student_id>/payments')
@role_required('admin', 'assistant')
def student_payments(student_id):
    student = Student.query.get_or_404(student_id)
    payments = Payment.query.filter_by(student_id=student_id).order_by(Payment.created_at.desc()).all()
    return render_template('admin/student_payments.html', student=student, payments=payments)

@bp.route('/students/<int:student_id>/payments/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_payment(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        from datetime import datetime
        
        due_date_str = request.form.get('due_date')
        due_date_obj = None
        if due_date_str:
            try:
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        payment = Payment(
            student_id=student_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            total_amount=float(request.form.get('total_amount')),
            due_date=due_date_obj,
            created_by_id=current_user.id
        )
        
        db.session.add(payment)
        db.session.commit()
        
        from app.utils.notifications import send_new_payment_notification
        send_new_payment_notification(payment.id)
        
        flash('تم إضافة القسط بنجاح وإرسال إشعار للطالب', 'success')
        return redirect(url_for('admin.student_payments', student_id=student_id))
    
    return render_template('admin/add_payment.html', student=student)

@bp.route('/payments/<int:payment_id>/installments/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_installment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        from datetime import datetime
        
        payment_date_str = request.form.get('payment_date')
        payment_date_obj = None
        if payment_date_str:
            try:
                payment_date_obj = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except ValueError:
                payment_date_obj = datetime.now().date()
        else:
            payment_date_obj = datetime.now().date()
        
        amount = float(request.form.get('amount'))
        
        if amount > payment.remaining_amount:
            flash('المبلغ المدفوع أكبر من المبلغ المتبقي', 'danger')
            return redirect(url_for('admin.add_installment', payment_id=payment_id))
        
        installment = InstallmentPayment(
            payment_id=payment_id,
            amount=amount,
            payment_date=payment_date_obj,
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes'),
            receipt_number=request.form.get('receipt_number'),
            created_by_id=current_user.id
        )
        
        payment.paid_amount += amount
        payment.update_status()
        
        db.session.add(installment)
        db.session.commit()
        
        from app.utils.notifications import send_payment_received_notification
        send_payment_received_notification(installment.id)
        
        flash('تم تسجيل الدفعة بنجاح وإرسال إشعار للطالب', 'success')
        return redirect(url_for('admin.student_payments', student_id=payment.student_id))
    
    return render_template('admin/add_installment.html', payment=payment)

@bp.route('/payments/<int:payment_id>/view')
@role_required('admin', 'assistant')
def view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    installments = InstallmentPayment.query.filter_by(payment_id=payment_id).order_by(InstallmentPayment.payment_date.desc()).all()
    return render_template('admin/view_payment.html', payment=payment, installments=installments)

@bp.route('/payments/<int:payment_id>/edit', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        from datetime import datetime
        
        due_date_str = request.form.get('due_date')
        due_date_obj = None
        if due_date_str:
            try:
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        payment.title = request.form.get('title')
        payment.description = request.form.get('description')
        payment.total_amount = float(request.form.get('total_amount'))
        payment.due_date = due_date_obj
        
        payment.update_status()
        db.session.commit()
        
        flash('تم تعديل القسط بنجاح', 'success')
        return redirect(url_for('admin.view_payment', payment_id=payment_id))
    
    return render_template('admin/edit_payment.html', payment=payment)

@bp.route('/payments/<int:payment_id>/delete', methods=['POST'])
@role_required('admin')
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    student_id = payment.student_id
    db.session.delete(payment)
    db.session.commit()
    flash('تم حذف القسط بنجاح', 'success')
    return redirect(url_for('admin.student_payments', student_id=student_id))

@bp.route('/installments/<int:installment_id>/edit', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_installment(installment_id):
    installment = InstallmentPayment.query.get_or_404(installment_id)
    payment = installment.payment
    
    if request.method == 'POST':
        from datetime import datetime
        
        old_amount = installment.amount
        new_amount = float(request.form.get('amount'))
        
        payment_date_str = request.form.get('payment_date')
        payment_date_obj = None
        if payment_date_str:
            try:
                payment_date_obj = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except ValueError:
                payment_date_obj = datetime.now().date()
        else:
            payment_date_obj = datetime.now().date()
        
        available_amount = payment.remaining_amount + old_amount
        if new_amount > available_amount:
            flash(f'المبلغ المدفوع أكبر من المبلغ المتاح ({available_amount:,.0f} ل.س)', 'danger')
            return redirect(url_for('admin.edit_installment', installment_id=installment_id))
        
        payment.paid_amount = payment.paid_amount - old_amount + new_amount
        
        installment.amount = new_amount
        installment.payment_date = payment_date_obj
        installment.payment_method = request.form.get('payment_method')
        installment.notes = request.form.get('notes')
        installment.receipt_number = request.form.get('receipt_number')
        
        payment.update_status()
        db.session.commit()
        
        flash('تم تعديل الدفعة بنجاح', 'success')
        return redirect(url_for('admin.view_payment', payment_id=payment.id))
    
    return render_template('admin/edit_installment.html', installment=installment, payment=payment)

@bp.route('/installments/<int:installment_id>/delete', methods=['POST'])
@role_required('admin')
def delete_installment(installment_id):
    installment = InstallmentPayment.query.get_or_404(installment_id)
    payment = installment.payment
    
    payment.paid_amount -= installment.amount
    payment.update_status()
    
    db.session.delete(installment)
    db.session.commit()
    
    flash('تم حذف الدفعة بنجاح', 'success')
    return redirect(url_for('admin.view_payment', payment_id=payment.id))

@bp.route('/settings/payment-reminders', methods=['GET', 'POST'])
@role_required('admin')
def payment_reminder_settings():
    settings = SiteSettings.query.first()
    
    if request.method == 'POST':
        settings.payment_reminder_enabled = request.form.get('payment_reminder_enabled') == 'on'
        settings.payment_reminder_days_before = int(request.form.get('payment_reminder_days_before', 3))
        settings.payment_reminder_time = request.form.get('payment_reminder_time', '09:00')
        settings.payment_reminder_message = request.form.get('payment_reminder_message', settings.payment_reminder_message)
        
        db.session.commit()
        
        from app.utils.scheduler import update_reminder_schedule
        update_reminder_schedule(settings.payment_reminder_time, settings.payment_reminder_enabled)
        
        flash('تم حفظ إعدادات التذكير بالأقساط بنجاح', 'success')
        return redirect(url_for('admin.payment_reminder_settings'))
    
    return render_template('admin/payment_reminder_settings.html', settings=settings)

@bp.route('/payments/all')
@role_required('admin', 'assistant')
def all_payments():
    status_filter = request.args.get('status', 'all')
    
    query = Payment.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/all_payments.html', payments=payments, status_filter=status_filter)

@bp.route('/payments/reports')
@role_required('admin', 'assistant')
def payment_reports():
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    all_payments = Payment.query.all()
    total_expected = sum(p.total_amount for p in all_payments)
    total_collected = sum(p.paid_amount for p in all_payments)
    total_remaining = total_expected - total_collected
    
    paid_count = Payment.query.filter_by(status='paid').count()
    partial_count = Payment.query.filter_by(status='partial').count()
    pending_count = Payment.query.filter_by(status='pending').count()
    total_count = Payment.query.count()
    
    students_with_payments = db.session.query(Student).join(Payment).distinct().count()
    students_with_pending = db.session.query(Student).join(Payment).filter(Payment.status.in_(['pending', 'partial'])).distinct().count()
    
    overdue_payments = Payment.query.filter(
        Payment.status.in_(['pending', 'partial']),
        Payment.due_date < datetime.now().date()
    ).all() if datetime.now().date() else []
    
    recent_payments = InstallmentPayment.query.order_by(InstallmentPayment.created_at.desc()).limit(10).all()
    
    payment_methods_stats = db.session.query(
        InstallmentPayment.payment_method,
        func.count(InstallmentPayment.id).label('count'),
        func.sum(InstallmentPayment.amount).label('total')
    ).group_by(InstallmentPayment.payment_method).all()
    
    last_30_days = datetime.now() - timedelta(days=30)
    monthly_collections_raw = db.session.query(
        func.date(InstallmentPayment.created_at).label('date'),
        func.sum(InstallmentPayment.amount).label('total')
    ).filter(InstallmentPayment.created_at >= last_30_days).group_by(func.date(InstallmentPayment.created_at)).all()
    
    monthly_collections = []
    for item in monthly_collections_raw:
        date_obj = datetime.strptime(str(item.date), '%Y-%m-%d').date() if item.date else None
        monthly_collections.append({
            'date': date_obj,
            'total': float(item.total) if item.total else 0
        })
    
    top_payments = Payment.query.order_by(Payment.total_amount.desc()).limit(5).all()
    
    stats = {
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_remaining': total_remaining,
        'collection_rate': (total_collected / total_expected * 100) if total_expected > 0 else 0,
        'paid_count': paid_count,
        'partial_count': partial_count,
        'pending_count': pending_count,
        'total_count': total_count,
        'students_with_payments': students_with_payments,
        'students_with_pending': students_with_pending,
        'overdue_count': len(overdue_payments),
        'overdue_amount': sum(p.remaining_amount for p in overdue_payments)
    }
    
    return render_template('admin/payment_reports.html',
                         stats=stats,
                         recent_payments=recent_payments,
                         payment_methods_stats=payment_methods_stats,
                         monthly_collections=monthly_collections,
                         top_payments=top_payments,
                         overdue_payments=overdue_payments)

@bp.route('/attendance')
@role_required('admin', 'assistant')
def attendance_list():
    from datetime import date, timedelta
    
    page = request.args.get('page', 1, type=int)
    user_type = request.args.get('user_type', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    user_id = request.args.get('user_id', type=int)
    
    query = Attendance.query
    
    if user_type:
        query = query.filter_by(user_type=user_type)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    attendance_records = query.order_by(Attendance.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    students = Student.query.all()
    teachers = Teacher.query.all()
    
    return render_template('admin/attendance_list.html',
                         attendance_records=attendance_records,
                         students=students,
                         teachers=teachers,
                         user_type=user_type,
                         status=status,
                         date_from=date_from,
                         date_to=date_to,
                         user_id=user_id)

@bp.route('/attendance/add', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def add_attendance():
    from datetime import date
    from app.utils.notifications import send_notification
    from sqlalchemy.exc import IntegrityError
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_type = request.form.get('user_type')
        attendance_date = request.form.get('date')
        status = request.form.get('status')
        notes = request.form.get('notes', '').strip()
        
        if not all([user_id, user_type, attendance_date, status]):
            flash('جميع الحقول المطلوبة يجب أن تكون معبأة', 'danger')
            return redirect(url_for('admin.add_attendance'))
        
        existing = Attendance.query.filter_by(
            user_id=user_id,
            date=attendance_date
        ).first()
        
        if existing:
            flash('يوجد سجل حضور لنفس المستخدم في هذا التاريخ', 'warning')
            return redirect(url_for('admin.add_attendance'))
        
        new_record = Attendance(
            user_id=user_id,
            user_type=user_type,
            date=attendance_date,
            status=status,
            notes=notes if notes else None
        )
        
        try:
            db.session.add(new_record)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('خطأ: يوجد سجل حضور لنفس المستخدم في هذا التاريخ', 'danger')
            return redirect(url_for('admin.add_attendance'))
        
        if status == 'absent':
            user = User.query.get(user_id)
            if user:
                absent_count = Attendance.query.filter_by(
                    user_id=user_id,
                    status='absent'
                ).count()
                
                title = "⚠️ تنبيه غياب"
                message = f"تم تسجيل غيابك بتاريخ {attendance_date}\nعدد أيام الغياب: {absent_count} يوم"
                if notes:
                    message += f"\nملاحظات: {notes}"
                
                send_notification(
                    title=title,
                    message=message,
                    user_ids=[user_id],
                    notification_type='absence_alert',
                    send_telegram=True,
                    send_web=True
                )
        
        flash('تم إضافة سجل الحضور بنجاح', 'success')
        return redirect(url_for('admin.attendance_list'))
    
    students = Student.query.all()
    teachers = Teacher.query.all()
    today = date.today().strftime('%Y-%m-%d')
    
    students_data = [{'id': s.id, 'user_id': s.user_id, 'full_name': s.user.full_name, 'student_number': s.student_number or ''} for s in students]
    teachers_data = [{'id': t.id, 'user_id': t.user_id, 'full_name': t.user.full_name, 'specialization': t.specialization or ''} for t in teachers]
    
    return render_template('admin/add_attendance.html',
                         students=students_data,
                         teachers=teachers_data,
                         today=today)

@bp.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@role_required('admin', 'assistant')
def edit_attendance(id):
    from app.utils.notifications import send_notification
    from sqlalchemy.exc import IntegrityError
    
    record = Attendance.query.get_or_404(id)
    
    if request.method == 'POST':
        attendance_date = request.form.get('date')
        status = request.form.get('status')
        notes = request.form.get('notes', '').strip()
        
        if not all([attendance_date, status]):
            flash('جميع الحقول المطلوبة يجب أن تكون معبأة', 'danger')
            return redirect(url_for('admin.edit_attendance', id=id))
        
        old_status = record.status
        
        record.date = attendance_date
        record.status = status
        record.notes = notes if notes else None
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('خطأ: يوجد سجل حضور آخر لنفس المستخدم في هذا التاريخ', 'danger')
            return redirect(url_for('admin.edit_attendance', id=id))
        
        if old_status != 'absent' and status == 'absent':
            user = User.query.get(record.user_id)
            if user:
                absent_count = Attendance.query.filter_by(
                    user_id=record.user_id,
                    status='absent'
                ).count()
                
                title = "⚠️ تنبيه غياب"
                message = f"تم تسجيل غيابك بتاريخ {attendance_date}\nعدد أيام الغياب: {absent_count} يوم"
                if notes:
                    message += f"\nملاحظات: {notes}"
                
                send_notification(
                    title=title,
                    message=message,
                    user_ids=[record.user_id],
                    notification_type='absence_alert',
                    send_telegram=True,
                    send_web=True
                )
        
        flash('تم تحديث سجل الحضور بنجاح', 'success')
        return redirect(url_for('admin.attendance_list'))
    
    return render_template('admin/edit_attendance.html', record=record)

@bp.route('/attendance/delete/<int:id>', methods=['POST'])
@role_required('admin', 'assistant')
def delete_attendance(id):
    record = Attendance.query.get_or_404(id)
    
    db.session.delete(record)
    db.session.commit()
    
    flash('تم حذف سجل الحضور بنجاح', 'success')
    return redirect(url_for('admin.attendance_list'))
