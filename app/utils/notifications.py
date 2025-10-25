import asyncio
import logging
from flask import current_app
from telegram import Bot
from telegram.constants import ParseMode
from app import db
from app.models import (Notification, NotificationRecipient, User, Student, Teacher, 
                       Enrollment, BotSession, SiteSettings)
from app.utils.helpers import damascus_now

logger = logging.getLogger(__name__)

async def send_telegram_notification_async(telegram_id: int, message: str, bot_token: str):
    try:
        bot = Bot(token=bot_token)
        result = await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        return result.message_id
    except Exception as e:
        logger.error(f"Error sending notification to {telegram_id}: {e}")
        return None

def create_notification(title, message, notification_type, created_by_id, 
                       target_type='all', target_id=None, 
                       send_telegram=True, send_web=True):
    notification = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        target_type=target_type,
        target_id=target_id,
        created_by=created_by_id,
        send_telegram=send_telegram,
        send_web=send_web
    )
    db.session.add(notification)
    db.session.commit()
    
    recipients = get_notification_recipients(target_type, target_id)
    
    for user in recipients:
        recipient = NotificationRecipient(
            notification_id=notification.id,
            user_id=user.id
        )
        db.session.add(recipient)
    
    db.session.commit()
    
    if send_telegram:
        send_telegram_notifications(notification.id)
    
    return notification


def get_notification_recipients(target_type, target_id=None):
    excluded_roles = ['admin', 'assistant']
    
    if target_type == 'all':
        return User.query.filter(User.is_active == True).filter(User.role.notin_(excluded_roles)).all()
    
    elif target_type == 'all_students':
        student_ids = db.session.query(Student.user_id).all()
        user_ids = [sid[0] for sid in student_ids]
        return User.query.filter(User.id.in_(user_ids)).filter(User.is_active == True).filter(User.role.notin_(excluded_roles)).all()
    
    elif target_type == 'all_teachers':
        teacher_ids = db.session.query(Teacher.user_id).all()
        user_ids = [tid[0] for tid in teacher_ids]
        return User.query.filter(User.id.in_(user_ids)).filter(User.is_active == True).filter(User.role.notin_(excluded_roles)).all()
    
    elif target_type == 'student' and target_id:
        student = Student.query.get(target_id)
        if student and student.user.is_active and student.user.role not in excluded_roles:
            return [student.user]
        return []
    
    elif target_type == 'teacher' and target_id:
        teacher = Teacher.query.get(target_id)
        if teacher and teacher.user.is_active and teacher.user.role not in excluded_roles:
            return [teacher.user]
        return []
    
    elif target_type == 'course' and target_id:
        enrollments = Enrollment.query.filter_by(course_id=target_id).all()
        user_ids = [e.student.user_id for e in enrollments if e.student.user.is_active]
        return User.query.filter(User.id.in_(user_ids)).filter(User.role.notin_(excluded_roles)).all()
    
    elif target_type == 'user' and target_id:
        user = User.query.get(target_id)
        if user and user.is_active and user.role not in excluded_roles:
            return [user]
        return []
    
    return []


def send_telegram_notifications(notification_id):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        notification = Notification.query.get(notification_id)
        if not notification or not notification.send_telegram:
            return
        
        settings = SiteSettings.query.first()
        if not settings or not settings.telegram_bot_token:
            return
        
        recipients = NotificationRecipient.query.filter_by(
            notification_id=notification_id,
            telegram_delivered=False
        ).all()
        
        for recipient in recipients:
            bot_session = BotSession.query.filter_by(
                user_id=recipient.user_id,
                is_authenticated=True
            ).first()
            
            if not bot_session:
                continue
            
            message = f"🔔 *{notification.title}*\n\n{notification.message}"
            
            try:
                message_id = asyncio.run(send_telegram_notification_async(
                    bot_session.telegram_id,
                    message,
                    settings.telegram_bot_token
                ))
                
                if message_id:
                    recipient.mark_telegram_delivered(message_id)
            except Exception as e:
                logger.error(f"Error sending telegram notification to user {recipient.user_id}: {e}")


def send_new_lesson_notification(lesson_id):
    from app.models import Lesson, Course
    
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return
    
    course = Course.query.get(lesson.course_id)
    if not course:
        return
    
    title = f"درس جديد: {lesson.title}"
    message = f"تم إضافة درس جديد في دورة {course.title}\n\n"
    message += f"📖 عنوان الدرس: {lesson.title}\n"
    if lesson.description:
        message += f"📝 الوصف: {lesson.description}\n"
    if lesson.file_path:
        message += f"\n📎 يوجد ملف مرفق"
    
    create_notification(
        title=title,
        message=message,
        notification_type='new_lesson',
        created_by_id=lesson.teacher.user_id if lesson.teacher else 1,
        target_type='course',
        target_id=lesson.course_id,
        send_telegram=True,
        send_web=True
    )


def send_new_grade_notification(grade_id):
    from app.models import Grade
    
    grade = Grade.query.get(grade_id)
    if not grade:
        return
    
    student = grade.student
    if not student:
        return
    
    title = "علامة جديدة"
    message = f"تم إضافة علامة جديدة لك\n\n"
    message += f"📚 المادة: {grade.course.title if grade.course else 'غير محدد'}\n"
    message += f"📊 العلامة: {grade.grade} من {grade.max_grade}\n"
    if grade.notes:
        message += f"💬 ملاحظات: {grade.notes}\n"
    
    create_notification(
        title=title,
        message=message,
        notification_type='new_grade',
        created_by_id=grade.teacher.user_id if grade.teacher else 1,
        target_type='student',
        target_id=student.id,
        send_telegram=True,
        send_web=True
    )


def send_updated_grade_notification(grade_id):
    from app.models import Grade
    
    grade = Grade.query.get(grade_id)
    if not grade:
        return
    
    student = grade.student
    if not student:
        return
    
    title = "تحديث علامة"
    message = f"تم تحديث علامتك\n\n"
    message += f"📚 المادة: {grade.course.title if grade.course else 'غير محدد'}\n"
    message += f"📊 العلامة الجديدة: {grade.grade} من {grade.max_grade}\n"
    if grade.notes:
        message += f"💬 ملاحظات: {grade.notes}\n"
    
    create_notification(
        title=title,
        message=message,
        notification_type='updated_grade',
        created_by_id=grade.teacher.user_id if grade.teacher else 1,
        target_type='student',
        target_id=student.id,
        send_telegram=True,
        send_web=True
    )


def get_user_notifications(user_id, unread_only=False, limit=50):
    query = NotificationRecipient.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    query = query.join(Notification).filter(Notification.is_active == True)
    query = query.order_by(NotificationRecipient.id.desc()).limit(limit)
    
    return query.all()


def get_unread_count(user_id):
    return NotificationRecipient.query.filter_by(
        user_id=user_id,
        is_read=False
    ).join(Notification).filter(Notification.is_active == True).count()


def mark_notification_as_read(recipient_id):
    recipient = NotificationRecipient.query.get(recipient_id)
    if recipient:
        recipient.mark_as_read(source='web')
        return True
    return False


def mark_all_as_read(user_id):
    recipients = NotificationRecipient.query.filter_by(
        user_id=user_id,
        is_read=False
    ).all()
    
    for recipient in recipients:
        recipient.mark_as_read(source='web')
    
    return len(recipients)


def send_new_payment_notification(payment_id):
    from app.models import Payment
    
    payment = Payment.query.get(payment_id)
    if not payment:
        return
    
    student = payment.student
    if not student:
        return
    
    title = "قسط جديد"
    message = f"تم إضافة قسط جديد لك\n\n"
    message += f"📋 العنوان: {payment.title}\n"
    message += f"💰 المبلغ الإجمالي: {payment.total_amount} ل.س\n"
    message += f"💳 المبلغ المدفوع: {payment.paid_amount} ل.س\n"
    message += f"📊 المبلغ المتبقي: {payment.remaining_amount} ل.س\n"
    if payment.due_date:
        message += f"📅 تاريخ الاستحقاق: {payment.due_date.strftime('%Y-%m-%d')}\n"
    if payment.description:
        message += f"📝 التفاصيل: {payment.description}\n"
    
    create_notification(
        title=title,
        message=message,
        notification_type='new_payment',
        created_by_id=payment.created_by_id if payment.created_by_id else 1,
        target_type='student',
        target_id=student.id,
        send_telegram=True,
        send_web=True
    )


def send_payment_received_notification(installment_id):
    from app.models import InstallmentPayment
    
    installment = InstallmentPayment.query.get(installment_id)
    if not installment:
        return
    
    payment = installment.payment
    if not payment:
        return
    
    student = payment.student
    if not student:
        return
    
    title = "تم استلام دفعة"
    message = f"تم تسجيل دفعة جديدة لحسابك\n\n"
    message += f"📋 القسط: {payment.title}\n"
    message += f"💵 المبلغ المدفوع: {installment.amount} ل.س\n"
    message += f"📅 تاريخ الدفع: {installment.payment_date.strftime('%Y-%m-%d')}\n"
    message += f"💳 المبلغ المدفوع الإجمالي: {payment.paid_amount} ل.س\n"
    message += f"📊 المبلغ المتبقي: {payment.remaining_amount} ل.س\n"
    
    if payment.is_paid:
        message += f"\n✅ تم تسديد القسط بالكامل"
    
    if installment.receipt_number:
        message += f"\n🧾 رقم الوصل: {installment.receipt_number}"
    
    create_notification(
        title=title,
        message=message,
        notification_type='payment_received',
        created_by_id=installment.created_by_id if installment.created_by_id else 1,
        target_type='student',
        target_id=student.id,
        send_telegram=True,
        send_web=True
    )


def send_payment_reminder_notification(payment_id):
    from app.models import Payment
    from app.models.settings import SiteSettings
    from datetime import datetime
    
    payment = Payment.query.get(payment_id)
    if not payment:
        return
    
    if payment.is_paid:
        return
    
    student = payment.student
    if not student:
        return
    
    settings = SiteSettings.query.first()
    
    is_overdue = False
    days_until_due = None
    if payment.due_date:
        from app.utils.helpers import damascus_now
        today = damascus_now().date()
        days_until_due = (payment.due_date - today).days
        is_overdue = days_until_due < 0
    
    if is_overdue:
        title = "⚠️ تنبيه: قسط متأخر"
    else:
        title = "تذكير بالقسط المستحق"
    
    if settings and settings.payment_reminder_message:
        message_template = settings.payment_reminder_message
        
        status_text = ""
        if is_overdue:
            status_text = f"\n⚠️ تأخر {abs(days_until_due)} يوم\n"
        elif days_until_due is not None:
            status_text = f"\n⏰ باقي {days_until_due} يوم على الاستحقاق\n"
        
        message = message_template.format(
            title=payment.title or '',
            total_amount=payment.total_amount or 0,
            paid_amount=payment.paid_amount or 0,
            remaining_amount=payment.remaining_amount or 0,
            due_date=payment.due_date.strftime('%Y-%m-%d') if payment.due_date else 'غير محدد',
            student_name=student.name or ''
        )
        message += status_text
    else:
        if is_overdue:
            message = f"⚠️ تنبيه هام: لديك قسط متأخر\n\n"
            message += f"⏱️ متأخر منذ: {abs(days_until_due)} يوم\n\n"
        else:
            message = f"تذكير: لديك قسط مستحق\n\n"
            if days_until_due is not None:
                message += f"⏰ المتبقي على الاستحقاق: {days_until_due} يوم\n\n"
        
        message += f"📋 العنوان: {payment.title}\n"
        message += f"💰 المبلغ الإجمالي: {payment.total_amount} ل.س\n"
        message += f"💳 المبلغ المدفوع: {payment.paid_amount} ل.س\n"
        message += f"📊 المبلغ المتبقي: {payment.remaining_amount} ل.س\n"
        
        if payment.due_date:
            message += f"📅 تاريخ الاستحقاق: {payment.due_date.strftime('%Y-%m-%d')}\n"
        
        if is_overdue:
            message += f"\n⚠️ يرجى التسديد فوراً لتجنب المزيد من التأخير!"
        else:
            message += f"\nيرجى تسديد المبلغ المتبقي في أقرب وقت ممكن."
    
    create_notification(
        title=title,
        message=message,
        notification_type='payment_reminder',
        created_by_id=1,
        target_type='student',
        target_id=student.id,
        send_telegram=True,
        send_web=True
    )


def send_notification(title, message, user_ids, notification_type, 
                     send_telegram=True, send_web=True, created_by_id=1):
    """
    Send notification to specific users by their user_ids
    """
    for user_id in user_ids:
        create_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            created_by_id=created_by_id,
            target_type='user',
            target_id=user_id,
            send_telegram=send_telegram,
            send_web=send_web
        )


def broadcast_message(message: str, role=None):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        settings = SiteSettings.query.first()
        
        if not settings or not settings.telegram_bot_enabled:
            return 0
        
        if not settings.telegram_bot_token:
            return 0
        
        query = BotSession.query.filter_by(is_authenticated=True)
        
        if role:
            query = query.join(User).filter(User.role == role)
        
        sessions = query.all()
        
        success_count = 0
        for session in sessions:
            try:
                asyncio.run(send_telegram_notification_async(
                    session.telegram_id,
                    message,
                    settings.telegram_bot_token
                ))
                success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {session.telegram_id}: {e}")
        
        return success_count
