from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Teacher, Student, Course, Enrollment, Lesson, Grade
from app.utils.decorators import role_required
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
    
    stats = {
        'courses': my_courses,
        'students': my_students,
        'lessons': my_lessons
    }
    
    return render_template('teacher/dashboard.html', teacher=teacher, stats=stats)

@bp.route('/lessons')
@role_required('teacher')
def lessons():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    all_lessons = Lesson.query.filter_by(teacher_id=teacher.id).all()
    return render_template('teacher/lessons.html', lessons=all_lessons)

@bp.route('/lessons/add', methods=['GET', 'POST'])
@role_required('teacher')
def add_lesson():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        description = request.form.get('description')
        
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
                lesson.file_type = filename.rsplit('.', 1)[1].lower()
        
        db.session.add(lesson)
        db.session.commit()
        flash('تم إضافة الدرس بنجاح', 'success')
        return redirect(url_for('teacher.lessons'))
    
    courses = Course.query.all()
    return render_template('teacher/add_lesson.html', courses=courses)

@bp.route('/students')
@role_required('teacher')
def students():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    my_students = Student.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/students.html', students=my_students)

@bp.route('/grades/add/<int:student_id>', methods=['GET', 'POST'])
@role_required('teacher')
def add_grade(student_id):
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        grade = Grade(
            student_id=student_id,
            course_id=request.form.get('course_id'),
            teacher_id=teacher.id,
            exam_name=request.form.get('exam_name'),
            grade=float(request.form.get('grade')),
            max_grade=float(request.form.get('max_grade')),
            notes=request.form.get('notes')
        )
        db.session.add(grade)
        db.session.commit()
        flash('تم إضافة الدرجة بنجاح', 'success')
        return redirect(url_for('teacher.students'))
    
    courses = Course.query.all()
    return render_template('teacher/add_grade.html', student=student, courses=courses)
