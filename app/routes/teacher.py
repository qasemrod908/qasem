from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Teacher, Student, Course, Enrollment, Lesson, Grade, NotificationRecipient, Notification, Attendance
from app.utils.decorators import role_required
from app.utils.notifications import get_user_notifications, get_unread_count, mark_notification_as_read
from werkzeug.utils import secure_filename
import os

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@bp.route('/dashboard')
@role_required('teacher')
def dashboard():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    my_courses = Enrollment.query.filter_by(teacher_id=teacher.id).count()
    my_students = Student.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).count()
    my_lessons = Lesson.query.filter_by(teacher_id=teacher.id).count()
    unread_notifications = get_unread_count(current_user.id)
    
    stats = {
        'courses': my_courses,
        'students': my_students,
        'lessons': my_lessons,
        'notifications': unread_notifications
    }
    
    recent_notifications = get_user_notifications(current_user.id, unread_only=False, limit=5)
    
    return render_template('teacher/dashboard.html', 
                          teacher=teacher, 
                          stats=stats,
                          recent_notifications=recent_notifications)

@bp.route('/lessons')
@role_required('teacher')
def lessons():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    all_lessons = Lesson.query.filter_by(teacher_id=teacher.id).all()
    return render_template('teacher/lessons.html', lessons=all_lessons)

@bp.route('/lessons/add', methods=['GET', 'POST'])
@role_required('teacher')
def add_lesson():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        description = request.form.get('description')
        
        enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=course_id).first()
        if not enrollment:
            flash('ليس لديك صلاحية لإضافة دروس لهذه الدورة', 'danger')
            return redirect(url_for('teacher.lessons'))
        
        lesson = Lesson(
            course_id=course_id,
            teacher_id=teacher.id,
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
                
                if '.' in filename:
                    lesson.file_type = filename.rsplit('.', 1)[1].lower()
                else:
                    lesson.file_type = 'unknown'
        
        db.session.add(lesson)
        db.session.commit()
        
        if lesson.is_published:
            from app.utils.notifications import send_new_lesson_notification
            send_new_lesson_notification(lesson.id)
        
        flash('تم إضافة الدرس بنجاح', 'success')
        return redirect(url_for('teacher.lessons'))
    
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/add_lesson.html', courses=enrolled_courses)

@bp.route('/students')
@role_required('teacher')
def students():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    my_students = Student.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/students.html', students=my_students)

@bp.route('/lessons/edit/<int:lesson_id>', methods=['GET', 'POST'])
@role_required('teacher')
def edit_lesson(lesson_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != teacher.id:
        flash('ليس لديك صلاحية لتعديل هذا الدرس', 'danger')
        return redirect(url_for('teacher.lessons'))
    
    if request.method == 'POST':
        new_course_id = request.form.get('course_id')
        
        if new_course_id != str(lesson.course_id):
            enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=new_course_id).first()
            if not enrollment:
                flash('ليس لديك صلاحية لنقل الدرس لهذه الدورة', 'danger')
                return redirect(url_for('teacher.edit_lesson', lesson_id=lesson_id))
        
        lesson.course_id = new_course_id
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
                
                if '.' in filename:
                    lesson.file_type = filename.rsplit('.', 1)[1].lower()
                else:
                    lesson.file_type = 'unknown'
        
        db.session.commit()
        flash('تم تحديث الدرس بنجاح', 'success')
        return redirect(url_for('teacher.lessons'))
    
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/edit_lesson.html', lesson=lesson, courses=enrolled_courses)

@bp.route('/lessons/delete/<int:lesson_id>', methods=['POST'])
@role_required('teacher')
def delete_lesson(lesson_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != teacher.id:
        flash('ليس لديك صلاحية لحذف هذا الدرس', 'danger')
        return redirect(url_for('teacher.lessons'))
    
    db.session.delete(lesson)
    db.session.commit()
    flash('تم حذف الدرس بنجاح', 'success')
    return redirect(url_for('teacher.lessons'))

@bp.route('/lessons/view/<int:course_id>')
@role_required('teacher')
def view_course_lessons(course_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    course = Course.query.get_or_404(course_id)
    
    teacher_enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=course_id).first()
    has_lessons_in_course = Lesson.query.filter_by(teacher_id=teacher.id, course_id=course_id).first()
    
    if not teacher_enrollment and not has_lessons_in_course:
        flash('ليس لديك صلاحية للوصول لدروس هذه الدورة', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    return render_template('teacher/view_lessons.html', course=course, lessons=lessons)

@bp.route('/lesson/download/<int:lesson_id>')
@role_required('teacher')
def download_lesson(lesson_id):
    from flask import send_file
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.teacher_id != teacher.id:
        teacher_enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=lesson.course_id).first()
        if not teacher_enrollment:
            flash('ليس لديك صلاحية لتحميل هذا الدرس', 'danger')
            return redirect(url_for('teacher.lessons'))
    
    if lesson.file_path:
        file_full_path = os.path.join(current_app.root_path, 'static', lesson.file_path)
        if os.path.exists(file_full_path):
            return send_file(file_full_path, as_attachment=True, download_name=os.path.basename(lesson.file_path))
        else:
            flash('الملف غير موجود', 'danger')
    else:
        flash('لا يوجد ملف مرفق لهذا الدرس', 'warning')
    
    return redirect(url_for('teacher.lessons'))

@bp.route('/grades/add/<int:student_id>', methods=['GET', 'POST'])
@role_required('teacher')
def add_grade(student_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        
        enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=course_id).first()
        if not enrollment:
            flash('ليس لديك صلاحية لإضافة درجات لهذه الدورة', 'danger')
            return redirect(url_for('teacher.students'))
        
        exam_date_str = request.form.get('exam_date')
        exam_date = None
        if exam_date_str:
            from datetime import datetime
            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
            except:
                pass
        
        grade = Grade(
            student_id=student_id,
            course_id=course_id,
            teacher_id=teacher.id,
            exam_name=request.form.get('exam_name'),
            grade=float(request.form.get('grade')),
            max_grade=float(request.form.get('max_grade')),
            notes=request.form.get('notes'),
            exam_date=exam_date
        )
        db.session.add(grade)
        db.session.commit()
        
        from app.utils.notifications import send_new_grade_notification
        send_new_grade_notification(grade.id)
        
        flash('تم إضافة الدرجة بنجاح', 'success')
        return redirect(url_for('teacher.view_student_grades', student_id=student_id))
    
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/add_grade.html', student=student, courses=enrolled_courses)

@bp.route('/students/<int:student_id>/grades')
@role_required('teacher')
def view_student_grades(student_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    student = Student.query.get_or_404(student_id)
    
    student_enrollment = Enrollment.query.filter_by(student_id=student_id, teacher_id=teacher.id).first()
    if not student_enrollment:
        flash('ليس لديك صلاحية لعرض درجات هذا الطالب', 'danger')
        return redirect(url_for('teacher.students'))
    
    grades = Grade.query.filter_by(student_id=student_id, teacher_id=teacher.id).order_by(Grade.created_at.desc()).all()
    
    return render_template('teacher/view_student_grades.html', student=student, grades=grades)

@bp.route('/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@role_required('teacher')
def edit_grade(grade_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    grade = Grade.query.get_or_404(grade_id)
    
    if grade.teacher_id != teacher.id:
        flash('ليس لديك صلاحية لتعديل هذه الدرجة', 'danger')
        return redirect(url_for('teacher.students'))
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        
        enrollment = Enrollment.query.filter_by(teacher_id=teacher.id, course_id=course_id).first()
        if not enrollment:
            flash('ليس لديك صلاحية لتعديل درجات لهذه الدورة', 'danger')
            return redirect(url_for('teacher.view_student_grades', student_id=grade.student_id))
        
        exam_date_str = request.form.get('exam_date')
        exam_date = None
        if exam_date_str:
            from datetime import datetime
            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
            except:
                pass
        
        grade.course_id = course_id
        grade.exam_name = request.form.get('exam_name')
        grade.grade = float(request.form.get('grade'))
        grade.max_grade = float(request.form.get('max_grade'))
        grade.notes = request.form.get('notes')
        grade.exam_date = exam_date
        
        db.session.commit()
        
        from app.utils.notifications import send_updated_grade_notification
        send_updated_grade_notification(grade.id)
        
        flash('تم تحديث الدرجة بنجاح', 'success')
        return redirect(url_for('teacher.view_student_grades', student_id=grade.student_id))
    
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/edit_grade.html', grade=grade, courses=enrolled_courses)

@bp.route('/grades/delete/<int:grade_id>', methods=['POST'])
@role_required('teacher')
def delete_grade(grade_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    grade = Grade.query.get_or_404(grade_id)
    
    if grade.teacher_id != teacher.id:
        flash('ليس لديك صلاحية لحذف هذه الدرجة', 'danger')
        return redirect(url_for('teacher.students'))
    
    student_id = grade.student_id
    db.session.delete(grade)
    db.session.commit()
    flash('تم حذف الدرجة بنجاح', 'success')
    return redirect(url_for('teacher.view_student_grades', student_id=student_id))

@bp.route('/notifications')
@role_required('teacher')
def notifications():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    all_notifications = get_user_notifications(current_user.id, unread_only=False, limit=50)
    unread_count = get_unread_count(current_user.id)
    
    return render_template('teacher/notifications.html', 
                          notifications=all_notifications,
                          unread_count=unread_count)

@bp.route('/notifications/read/<int:recipient_id>', methods=['POST'])
@role_required('teacher')
def mark_notification_read(recipient_id):
    recipient = NotificationRecipient.query.get_or_404(recipient_id)
    
    if recipient.user_id != current_user.id:
        flash('ليس لديك صلاحية لهذا الإجراء', 'danger')
        return redirect(url_for('teacher.notifications'))
    
    mark_notification_as_read(recipient_id)
    flash('تم تحديد الإشعار كمقروء', 'success')
    return redirect(url_for('teacher.notifications'))

@bp.route('/api/notifications/unread', methods=['GET'])
@role_required('teacher')
def api_get_unread_notifications():
    try:
        unread_notifications = get_user_notifications(current_user.id, unread_only=True, limit=10)
        unread_count = get_unread_count(current_user.id)
        
        notifications_data = []
        for recipient in unread_notifications:
            notif = recipient.notification
            if notif:
                notifications_data.append({
                    'id': recipient.id,
                    'notification_id': notif.id,
                    'title': notif.title or 'إشعار',
                    'message': notif.message or '',
                    'type': notif.notification_type,
                    'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M') if notif.created_at else '',
                    'is_read': recipient.is_read
                })
        
        return jsonify({
            'success': True,
            'count': unread_count,
            'notifications': notifications_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/notifications/mark-read/<int:recipient_id>', methods=['POST'])
@role_required('teacher')
def api_mark_notification_read(recipient_id):
    try:
        recipient = NotificationRecipient.query.get(recipient_id)
        
        if not recipient:
            return jsonify({
                'success': False,
                'error': 'الإشعار غير موجود'
            }), 404
        
        if recipient.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'ليس لديك صلاحية لهذا الإجراء'
            }), 403
        
        mark_notification_as_read(recipient_id)
        
        return jsonify({
            'success': True,
            'message': 'تم تحديد الإشعار كمقروء'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/attendance')
@role_required('teacher')
def attendance():
    from datetime import date, timedelta
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('الملف الشخصي للمعلم غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Attendance.query.filter_by(user_id=current_user.id)
    
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    
    attendance_records = query.order_by(Attendance.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    stats = Attendance.get_user_stats(current_user.id)
    
    thirty_days_ago = date.today() - timedelta(days=365)
    recent_stats = Attendance.get_user_stats(
        current_user.id, 
        start_date=thirty_days_ago
    )
    
    return render_template('teacher/attendance.html',
                         attendance_records=attendance_records,
                         stats=stats,
                         recent_stats=recent_stats,
                         date_from=date_from,
                         date_to=date_to)
