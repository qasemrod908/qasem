from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Student, Enrollment, Lesson, Grade, Course
from app.utils.decorators import role_required

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
    
    stats = {
        'courses': my_courses,
        'grades': total_grades
    }
    
    return render_template('student/dashboard.html', student=student, stats=stats)

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
