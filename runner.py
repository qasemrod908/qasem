import threading
import logging
import sys
from app import create_app, db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

flask_app = None
bot_thread = None
flask_thread = None

def run_flask():
    """تشغيل Flask App"""
    global flask_app
    try:
        flask_app = create_app()
        with flask_app.app_context():
            db.create_all()
        logger.info("Starting Flask application on port 5000...")
        flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        import traceback
        traceback.print_exc()

def run_telegram_bot():
    """تشغيل Telegram Bot"""
    try:
        logger.info("Starting Telegram Bot...")
        import bot
        bot.main()
    except Exception as e:
        logger.error(f"Error running Telegram bot: {e}")
        import traceback
        traceback.print_exc()

def main():
    """تشغيل كل من Flask وTelegram Bot معاً"""
    global flask_thread
    
    logger.info("=" * 50)
    logger.info("بدء تشغيل النظام المتكامل")
    logger.info("=" * 50)
    
    flask_thread = threading.Thread(target=run_flask, name="FlaskThread", daemon=True)
    
    flask_thread.start()
    logger.info("✓ تم بدء تشغيل Flask App في thread منفصل")
    
    logger.info("✓ بدء تشغيل Telegram Bot في main thread...")
    logger.info("=" * 50)
    logger.info("النظام يعمل الآن! اضغط Ctrl+C للإيقاف")
    logger.info("=" * 50)
    
    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 50)
        logger.info("إيقاف النظام...")
        logger.info("=" * 50)
        sys.exit(0)

if __name__ == '__main__':
    main()
