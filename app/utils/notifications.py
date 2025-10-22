import asyncio
import logging
from telegram import Bot
from telegram.constants import ParseMode
from app.models import BotSession, Student, Enrollment, SiteSettings
from app import db

logger = logging.getLogger(__name__)

async def send_telegram_notification(telegram_id: int, message: str, bot_token: str):
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        return True
    except Exception as e:
        logger.error(f"Error sending notification to {telegram_id}: {e}")
        return False

def notify_new_lesson(lesson_id: int, course_id: int):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        settings = SiteSettings.query.first()
        
        if not settings or not settings.telegram_bot_enabled or not settings.telegram_bot_notifications_enabled:
            return
        
        if not settings.telegram_bot_token:
            return
        
        from app.models import Lesson, Course
        
        lesson = Lesson.query.get(lesson_id)
        course = Course.query.get(course_id)
        
        if not lesson or not course:
            return
        
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        
        for enrollment in enrollments:
            student = enrollment.student
            if not student or not student.user:
                continue
            
            bot_session = BotSession.query.filter_by(user_id=student.user_id).first()
            if not bot_session or not bot_session.is_authenticated:
                continue
            
            message = f"""
🆕 *درس جديد متاح!*

📚 الدورة: {course.name}
📖 الدرس: {lesson.title}

{lesson.description if lesson.description else ''}

يمكنك الوصول إليه من خلال /mycourses
"""
            
            try:
                asyncio.run(send_telegram_notification(
                    bot_session.telegram_id,
                    message,
                    settings.telegram_bot_token
                ))
            except Exception as e:
                logger.error(f"Error notifying student {student.id}: {e}")

def notify_new_grade(grade_id: int):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        settings = SiteSettings.query.first()
        
        if not settings or not settings.telegram_bot_enabled or not settings.telegram_bot_notifications_enabled:
            return
        
        if not settings.telegram_bot_token:
            return
        
        from app.models import Grade, Course
        
        grade = Grade.query.get(grade_id)
        
        if not grade:
            return
        
        student = grade.student
        course = grade.course
        
        if not student or not student.user or not course:
            return
        
        bot_session = BotSession.query.filter_by(user_id=student.user_id).first()
        if not bot_session or not bot_session.is_authenticated:
            return
        
        message = f"""
📝 *تم إضافة درجة جديدة!*

📚 الدورة: {course.name}
📋 الامتحان: {grade.exam_name}
✅ الدرجة: {grade.score}/{grade.max_score}

يمكنك الاطلاع على جميع درجاتك من خلال /mygrades
"""
        
        try:
            asyncio.run(send_telegram_notification(
                bot_session.telegram_id,
                message,
                settings.telegram_bot_token
            ))
        except Exception as e:
            logger.error(f"Error notifying student {student.id} about grade: {e}")

def notify_enrollment(enrollment_id: int):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        settings = SiteSettings.query.first()
        
        if not settings or not settings.telegram_bot_enabled or not settings.telegram_bot_notifications_enabled:
            return
        
        if not settings.telegram_bot_token:
            return
        
        from app.models import Enrollment, Course
        
        enrollment = Enrollment.query.get(enrollment_id)
        
        if not enrollment:
            return
        
        student = enrollment.student
        course = enrollment.course
        teacher = enrollment.teacher
        
        if not student or not student.user or not course:
            return
        
        bot_session = BotSession.query.filter_by(user_id=student.user_id).first()
        if not bot_session or not bot_session.is_authenticated:
            return
        
        teacher_name = teacher.full_name if teacher else 'غير محدد'
        
        message = f"""
🎉 *تم تسجيلك في دورة جديدة!*

📚 اسم الدورة: {course.name}
👨‍🏫 المعلم: {teacher_name}
⏱️ المدة: {course.duration}

يمكنك الوصول إلى الدورة من خلال /mycourses

نتمنى لك التوفيق! 🌟
"""
        
        try:
            asyncio.run(send_telegram_notification(
                bot_session.telegram_id,
                message,
                settings.telegram_bot_token
            ))
        except Exception as e:
            logger.error(f"Error notifying student {student.id} about enrollment: {e}")

def broadcast_message(message: str, role=None):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        settings = SiteSettings.query.first()
        
        if not settings or not settings.telegram_bot_enabled:
            return
        
        if not settings.telegram_bot_token:
            return
        
        from app.models import User
        
        query = BotSession.query.filter_by(is_authenticated=True)
        
        if role:
            query = query.join(User).filter(User.role == role)
        
        sessions = query.all()
        
        success_count = 0
        for session in sessions:
            try:
                asyncio.run(send_telegram_notification(
                    session.telegram_id,
                    message,
                    settings.telegram_bot_token
                ))
                success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {session.telegram_id}: {e}")
        
        return success_count
