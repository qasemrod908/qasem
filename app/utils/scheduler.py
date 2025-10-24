import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app import db
from app.models import Payment, SiteSettings
from app.utils.notifications import send_payment_reminder_notification
from app.utils.helpers import damascus_now

logger = logging.getLogger(__name__)

scheduler = None


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
