from app import db
from sqlalchemy import inspect, text
import logging

logger = logging.getLogger(__name__)

def initialize_database():
    inspector = inspect(db.engine)
    
    if 'site_settings' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('site_settings')]
        
        with db.engine.begin() as connection:
            if 'telegram_bot_enabled' not in columns:
                logger.info("Adding telegram_bot_enabled column to site_settings")
                connection.execute(text("ALTER TABLE site_settings ADD COLUMN telegram_bot_enabled BOOLEAN DEFAULT 0"))
            
            if 'telegram_bot_webhook_enabled' not in columns:
                logger.info("Adding telegram_bot_webhook_enabled column to site_settings")
                connection.execute(text("ALTER TABLE site_settings ADD COLUMN telegram_bot_webhook_enabled BOOLEAN DEFAULT 0"))
            
            if 'telegram_bot_webhook_url' not in columns:
                logger.info("Adding telegram_bot_webhook_url column to site_settings")
                connection.execute(text("ALTER TABLE site_settings ADD COLUMN telegram_bot_webhook_url VARCHAR(500)"))
            
            if 'telegram_bot_notifications_enabled' not in columns:
                logger.info("Adding telegram_bot_notifications_enabled column to site_settings")
                connection.execute(text("ALTER TABLE site_settings ADD COLUMN telegram_bot_notifications_enabled BOOLEAN DEFAULT 1"))
    
    if 'bot_sessions' not in inspector.get_table_names():
        logger.info("Creating bot_sessions table")
        with db.engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE bot_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    user_id INTEGER,
                    is_authenticated BOOLEAN DEFAULT 0,
                    phone_number VARCHAR(20),
                    last_command VARCHAR(50),
                    conversation_state VARCHAR(50),
                    temp_data TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_bot_sessions_telegram_id ON bot_sessions (telegram_id)"))
    
    if 'bot_statistics' not in inspector.get_table_names():
        logger.info("Creating bot_statistics table")
        with db.engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE bot_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_users INTEGER DEFAULT 0,
                    active_users_today INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    messages_received INTEGER DEFAULT 0,
                    date DATE UNIQUE,
                    updated_at TIMESTAMP
                )
            """))
    
    if 'notifications' not in inspector.get_table_names():
        logger.info("Creating notifications table")
        with db.engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    target_type VARCHAR(50) NOT NULL,
                    target_id INTEGER,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP,
                    send_telegram BOOLEAN DEFAULT 1,
                    send_web BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """))
    
    if 'notification_recipients' not in inspector.get_table_names():
        logger.info("Creating notification_recipients table")
        with db.engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE notification_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    read_at TIMESTAMP,
                    telegram_delivered BOOLEAN DEFAULT 0,
                    telegram_delivered_at TIMESTAMP,
                    web_delivered BOOLEAN DEFAULT 0,
                    web_delivered_at TIMESTAMP,
                    telegram_message_id INTEGER,
                    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_recipients_user_id ON notification_recipients (user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_recipients_notification_id ON notification_recipients (notification_id)"))
    
    logger.info("Database initialization completed successfully")
