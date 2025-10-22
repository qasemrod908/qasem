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

@bp.route('/teacher/<int:teacher_id>')
def teacher_detail(teacher_id):
    settings = SiteSettings.query.first()
    teacher = Teacher.query.get_or_404(teacher_id)
    return render_template('public/teacher_detail.html', settings=settings, teacher=teacher)

@bp.route('/news')
def news():
    settings = SiteSettings.query.first()
    all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('public/news.html', settings=settings, news=all_news)

@bp.route('/news/<int:news_id>')
def news_detail(news_id):
    settings = SiteSettings.query.first()
    news_item = News.query.get_or_404(news_id)
    return render_template('public/news_detail.html', settings=settings, news=news_item)

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
        
        if settings and settings.telegram_bot_token and settings.telegram_chat_id:
            import threading
            import asyncio
            from telegram import Bot
            
            def send_contact_notification_async():
                async def send_notification():
                    try:
                        bot = Bot(token=settings.telegram_bot_token)
                        message_text = f"""
📧 رسالة جديدة من موقع المعهد

👤 الاسم: {contact_msg.name}
📧 البريد: {contact_msg.email or 'غير محدد'}
📞 الهاتف: {contact_msg.phone or 'غير محدد'}
📌 الموضوع: {contact_msg.subject}

💬 الرسالة:
{contact_msg.message}

⏰ التاريخ: {contact_msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
                        await bot.send_message(
                            chat_id=settings.telegram_chat_id,
                            text=message_text
                        )
                    except Exception as e:
                        print(f'خطأ في إرسال الإشعار إلى Telegram: {str(e)}')
                
                asyncio.run(send_notification())
            
            thread = threading.Thread(target=send_contact_notification_async)
            thread.start()
        
        flash('تم إرسال رسالتك بنجاح. سنتواصل معك قريباً', 'success')
        return redirect(url_for('public.contact'))
    
    return render_template('public/contact.html', settings=settings)
