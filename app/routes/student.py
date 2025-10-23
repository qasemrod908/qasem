from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Student, Enrollment, Lesson, Grade, Course, NotificationRecipient, Notification
from app.utils.decorators import role_required
from app.utils.notifications import get_user_notifications, get_unread_count, mark_notification_as_read

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/dashboard')
@role_required('student')
def dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('الملف الشخصي للطالب غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    my_courses = Enrollment.query.filter_by(student_id=student.id).count()
    total_grades = Grade.query.filter_by(student_id=student.id).count()
    unread_notifications = get_unread_count(current_user.id)
    
    stats = {
        'courses': my_courses,
        'grades': total_grades,
        'notifications': unread_notifications
    }
    
    recent_notifications = get_user_notifications(current_user.id, unread_only=False, limit=5)
    
    return render_template('student/dashboard.html', 
                          student=student, 
                          stats=stats,
                          recent_notifications=recent_notifications)

@bp.route('/courses')
@role_required('student')
def courses():
    student = Student.query.filter_by(user_id=current_user.id).first()
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    return render_template('student/courses.html', enrollments=enrollments)

@bp.route('/lessons/<int:course_id>')
@role_required('student')
def lessons(course_id):
    student = Student.query.filter_by(user_id=current_user.id).first()
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course_id).first_or_404()
    
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id, is_published=True).all()
    
    return render_template('student/lessons.html', course=course, lessons=lessons)

@bp.route('/grades')
@role_required('student')
def grades():
    student = Student.query.filter_by(user_id=current_user.id).first()
    my_grades = Grade.query.filter_by(student_id=student.id).order_by(Grade.created_at.desc()).all()
    return render_template('student/grades.html', grades=my_grades)

@bp.route('/lesson/download/<int:lesson_id>')
@role_required('student')
def download_lesson(lesson_id):
    from flask import send_file, current_app
    import os
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('الملف الشخصي للطالب غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=lesson.course_id).first()
    if not enrollment:
        flash('ليس لديك صلاحية لتحميل هذا الدرس', 'danger')
        return redirect(url_for('student.courses'))
    
    if lesson.file_path:
        file_full_path = os.path.join(current_app.root_path, 'static', lesson.file_path)
        if os.path.exists(file_full_path):
            return send_file(file_full_path, as_attachment=True, download_name=os.path.basename(lesson.file_path))
        else:
            flash('الملف غير موجود', 'danger')
    else:
        flash('لا يوجد ملف مرفق لهذا الدرس', 'warning')
    
    return redirect(url_for('student.lessons', course_id=lesson.course_id))

@bp.route('/notifications')
@role_required('student')
def notifications():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('الملف الشخصي للطالب غير موجود', 'danger')
        return redirect(url_for('public.index'))
    
    all_notifications = get_user_notifications(current_user.id, unread_only=False, limit=50)
    unread_count = get_unread_count(current_user.id)
    
    return render_template('student/notifications.html', 
                          notifications=all_notifications,
                          unread_count=unread_count)

@bp.route('/notifications/read/<int:recipient_id>', methods=['POST'])
@role_required('student')
def mark_notification_read(recipient_id):
    recipient = NotificationRecipient.query.get_or_404(recipient_id)
    
    if recipient.user_id != current_user.id:
        flash('ليس لديك صلاحية لهذا الإجراء', 'danger')
        return redirect(url_for('student.notifications'))
    
    mark_notification_as_read(recipient_id)
    flash('تم تحديد الإشعار كمقروء', 'success')
    return redirect(url_for('student.notifications'))
