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
        from werkzeug.security import safe_join
        
        safe_filename = os.path.basename(filename)
        file_path = safe_join('backups', safe_filename)
        
        if file_path is None or not file_path.startswith(os.path.abspath('backups')):
            flash('محاولة وصول غير مصرح بها', 'danger')
            return redirect(url_for('admin.backup'))
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('الملف غير موجود', 'danger')
            return redirect(url_for('admin.backup'))
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
        site_settings.telegram_bot_token = request.form.get('telegram_bot_token')
        site_settings.telegram_chat_id = request.form.get('telegram_chat_id')
        site_settings.telegram_backup_enabled = request.form.get('telegram_backup_enabled') == 'on'
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
        
        dob = request.form.get('date_of_birth')
        if dob:
            from datetime import datetime
            student.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        
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
    
    return render_template('admin/edit_student.html', student=student)

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

@bp.route('/students/enroll/<int:student_id>', methods=['POST'])
@role_required('admin', 'assistant')
def enroll_student(student_id):
    student = Student.query.get_or_404(student_id)
    course_id = request.form.get('course_id')
    teacher_id = request.form.get('teacher_id')
    
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if existing:
        flash('الطالب مسجل بالفعل في هذه الدورة', 'warning')
        return redirect(url_for('admin.students'))
    
    enrollment = Enrollment(
        student_id=student_id,
        course_id=course_id,
        teacher_id=teacher_id if teacher_id else None
    )
    db.session.add(enrollment)
    db.session.commit()
    flash('تم تسجيل الطالب في الدورة بنجاح', 'success')
    return redirect(url_for('admin.students'))

@bp.route('/students/unenroll/<int:enrollment_id>', methods=['POST'])
@role_required('admin', 'assistant')
def unenroll_student(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('تم إلغاء تسجيل الطالب من الدورة بنجاح', 'success')
    return redirect(url_for('admin.students'))

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
