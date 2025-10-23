import asyncio
import logging
from telegram import Bot
from telegram.constants import ParseMode
from app.models import Notification, NotificationRecipient, BotSession, SiteSettings
from app import db

logger = logging.getLogger(__name__)

async def send_single_telegram_notification(telegram_id, message, bot_token):
    try:
        bot = Bot(token=bot_token)
        result = await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        return result.message_id
    except Exception as e:
        logger.error(f"Error sending Telegram notification to {telegram_id}: {e}")
        return None

def send_telegram_notifications(notification_id):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        notification = Notification.query.get(notification_id)
        if not notification or not notification.send_telegram:
            return 0
        
        settings = SiteSettings.query.first()
        if not settings or not settings.telegram_bot_token:
            return 0
        
        recipients = NotificationRecipient.query.filter_by(
            notification_id=notification_id,
            telegram_delivered=False
        ).all()
        
        success_count = 0
        
        for recipient in recipients:
            bot_session = BotSession.query.filter_by(
                user_id=recipient.user_id,
                is_authenticated=True
            ).first()
            
            if not bot_session:
                continue
            
            message = f"🔔 *{notification.title}*\n\n{notification.message}"
            
            try:
                message_id = asyncio.run(send_single_telegram_notification(
                    bot_session.telegram_id,
                    message,
                    settings.telegram_bot_token
                ))
                
                if message_id:
                    recipient.mark_telegram_delivered(message_id)
                    success_count += 1
            except Exception as e:
                logger.error(f"Error sending telegram notification to user {recipient.user_id}: {e}")
        
        return success_count
