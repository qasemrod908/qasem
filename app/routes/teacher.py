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
        
        grade = Grade(
            student_id=student_id,
            course_id=course_id,
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
    
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.teacher_id == teacher.id).all()
    return render_template('teacher/add_grade.html', student=student, courses=enrolled_courses)
