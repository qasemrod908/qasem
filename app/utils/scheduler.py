import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app import db
from app.models import Payment, SiteSettings
from app.utils.notifications import send_payment_reminder_notification
from app.utils.helpers import damascus_now
import os

logger = logging.getLogger(__name__)

scheduler = None

failed_backup_path = None


def check_payment_reminders():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            settings = SiteSettings.query.first()
            
            if not settings or not settings.payment_reminder_enabled:
                return
            
            days_before = settings.payment_reminder_days_before
            today = damascus_now().date()
            target_date = today + timedelta(days=days_before)
            
            payments = Payment.query.filter(
                Payment.status.in_(['pending', 'partial']),
                Payment.due_date <= target_date
            ).all()
            
            for payment in payments:
                if not payment.is_paid:
                    send_payment_reminder_notification(payment.id)
                    logger.info(f"Sent payment reminder for payment {payment.id}")
            
            logger.info(f"Payment reminder check completed. Sent {len(payments)} reminders.")
            
        except Exception as e:
            logger.error(f"Error in check_payment_reminders: {e}")


def daily_telegram_backup():
    """نسخ احتياطي يومي مع إرسال إلى تيليجرام وحذف من السيرفر"""
    global failed_backup_path
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            from app.utils.backup import BackupManager
            
            # إذا كان هناك نسخة فاشلة سابقة، نحاول إرسالها أولاً
            if failed_backup_path and os.path.exists(failed_backup_path):
                logger.info(f"محاولة إعادة إرسال النسخة الفاشلة: {failed_backup_path}")
                from app.models.settings import SiteSettings
                settings = SiteSettings.query.first()
                
                if settings and settings.telegram_bot_token and settings.telegram_chat_id:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    success = loop.run_until_complete(
                        BackupManager.send_to_telegram(
                            failed_backup_path,
                            settings.telegram_bot_token,
                            settings.telegram_chat_id
                        )
                    )
                    loop.close()
                    
                    if success:
                        logger.info(f"تم إرسال النسخة الفاشلة بنجاح: {failed_backup_path}")
                        try:
                            os.remove(failed_backup_path)
                            failed_backup_path = None
                            logger.info(f"تم حذف النسخة المحلية: {failed_backup_path}")
                        except Exception as e:
                            logger.error(f"خطأ في حذف النسخة المحلية: {e}")
            
            # إنشاء وإرسال النسخة الجديدة
            success = BackupManager.create_and_send_telegram_backup()
            
            if success:
                logger.info("تم النسخ الاحتياطي اليومي وإرساله إلى تيليجرام بنجاح")
                failed_backup_path = None
            else:
                # في حالة الفشل، نحتفظ بمسار الملف لإعادة المحاولة لاحقاً
                logger.warning("فشل النسخ الاحتياطي أو الإرسال، سيتم إعادة المحاولة في المرة القادمة")
                # البحث عن آخر نسخة احتياطية تم إنشاؤها
                if os.path.exists('backups'):
                    backups = sorted([f for f in os.listdir('backups') if f.endswith('.zip')], reverse=True)
                    if backups:
                        failed_backup_path = os.path.join('backups', backups[0])
                        logger.info(f"تم حفظ مسار النسخة الفاشلة: {failed_backup_path}")
            
        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي اليومي: {e}")
            import traceback
            traceback.print_exc()


def init_scheduler(app):
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler(daemon=True)
        
        with app.app_context():
            settings = SiteSettings.query.first()
            
            if settings and settings.payment_reminder_enabled:
                reminder_time = settings.payment_reminder_time or '09:00'
                hour, minute = map(int, reminder_time.split(':'))
                
                scheduler.add_job(
                    func=check_payment_reminders,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    id='payment_reminder_job',
                    name='Daily Payment Reminder',
                    replace_existing=True
                )
                
                logger.info(f"Payment reminder scheduler initialized at {reminder_time}")
            
            # إضافة النسخ الاحتياطي اليومي في الساعة 9 مساءً (21:00)
            if settings and settings.telegram_backup_enabled:
                scheduler.add_job(
                    func=daily_telegram_backup,
                    trigger=CronTrigger(hour=21, minute=0),
                    id='daily_telegram_backup_job',
                    name='Daily Telegram Backup',
                    replace_existing=True
                )
                
                logger.info("Daily Telegram backup scheduler initialized at 21:00 (9 PM)")
        
        scheduler.start()
        logger.info("Scheduler started successfully")


def update_reminder_schedule(reminder_time, enabled=True):
    global scheduler
    
    if scheduler is None:
        return False
    
    try:
        if not enabled:
            try:
                scheduler.remove_job('payment_reminder_job')
                logger.info("Payment reminder job removed")
            except:
                pass
            return True
        
        hour, minute = map(int, reminder_time.split(':'))
        
        try:
            scheduler.reschedule_job(
                job_id='payment_reminder_job',
                trigger=CronTrigger(hour=hour, minute=minute)
            )
            logger.info(f"Payment reminder schedule updated to {reminder_time}")
        except:
            scheduler.add_job(
                func=check_payment_reminders,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='payment_reminder_job',
                name='Daily Payment Reminder',
                replace_existing=True
            )
            logger.info(f"Payment reminder job created at {reminder_time}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating reminder schedule: {e}")
        return False


def shutdown_scheduler():
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler shut down successfully")
