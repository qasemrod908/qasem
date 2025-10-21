from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import db
from app.models import SiteSettings, Course, Teacher, News, Testimonial, Certificate, Contact

bp = Blueprint('public', __name__)

@bp.route('/')
def index():
    settings = SiteSettings.query.first()
    featured_courses = Course.query.filter_by(is_featured=True).limit(6).all()
    teachers = Teacher.query.limit(4).all()
    news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
    testimonials = Testimonial.query.filter_by(is_published=True).limit(4).all()
    certificates = Certificate.query.filter_by(is_published=True).order_by(Certificate.display_order).all()
    
    return render_template('public/index.html',
                         settings=settings,
                         featured_courses=featured_courses,
                         teachers=teachers,
                         news=news,
                         testimonials=testimonials,
                         certificates=certificates)

@bp.route('/courses')
def courses():
    settings = SiteSettings.query.first()
    all_courses = Course.query.all()
    return render_template('public/courses.html', settings=settings, courses=all_courses)

@bp.route('/course/<int:course_id>')
def course_detail(course_id):
    settings = SiteSettings.query.first()
    course = Course.query.get_or_404(course_id)
    return render_template('public/course_detail.html', settings=settings, course=course)

@bp.route('/teachers')
def teachers():
    settings = SiteSettings.query.first()
    all_teachers = Teacher.query.all()
    return render_template('public/teachers.html', settings=settings, teachers=all_teachers)

@bp.route('/news')
def news():
    settings = SiteSettings.query.first()
    all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('public/news.html', settings=settings, news=all_news)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    settings = SiteSettings.query.first()
    
    if request.method == 'POST':
        contact_msg = Contact(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            subject=request.form.get('subject'),
            message=request.form.get('message')
        )
        db.session.add(contact_msg)
        db.session.commit()
        flash('تم إرسال رسالتك بنجاح. سنتواصل معك قريباً', 'success')
        return redirect(url_for('public.contact'))
    
    return render_template('public/contact.html', settings=settings)
