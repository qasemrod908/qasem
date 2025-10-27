from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from sqlalchemy import event
import threading
import logging

db = SQLAlchemy()
login_manager = LoginManager()

def setup_auto_backup():
    watched_tables = {
        'users', 'students', 'teachers',
        'courses', 'enrollments', 'lessons', 'sections', 'class_grades',
        'grades', 'certificates',
        'news', 'testimonials',
        'contacts', 'site_settings'
    }
    
    modified_tables = set()
    
    @event.listens_for(db.session, 'before_commit')
    def receive_before_commit(session):
        for obj in session.new:
            table_name = obj.__tablename__
            if table_name in watched_tables:
                modified_tables.add(table_name)
        
        for obj in session.dirty:
            table_name = obj.__tablename__
            if table_name in watched_tables:
                modified_tables.add(table_name)
        
        for obj in session.deleted:
            table_name = obj.__tablename__
            if table_name in watched_tables:
                modified_tables.add(table_name)
    
    app_instance = None
    
    @event.listens_for(db.session, 'after_commit')
    def receive_after_commit(session):
        nonlocal modified_tables, app_instance
        
        if modified_tables:
            logging.info(f'🔄 تم تعديل الجداول التالية: {", ".join(modified_tables)}')
            tables_copy = modified_tables.copy()
            modified_tables.clear()
            
            if app_instance is None:
                try:
                    from flask import current_app
                    app_instance = current_app._get_current_object()
                    logging.info(f'✅ تم الحصول على سياق التطبيق')
                except Exception as e:
                    logging.error(f'❌ خطأ في الحصول على سياق التطبيق: {e}')
                    return
            
            def auto_backup():
                try:
                    logging.info('📦 بدء عملية النسخ الاحتياطي التلقائي...')
                    with app_instance.app_context():
                        from app.utils.backup import BackupManager
                        result = BackupManager.create_and_send_telegram_backup()
                        if result:
                            logging.info('✅ تم إرسال النسخة الاحتياطية إلى تيليجرام بنجاح')
                        else:
                            logging.warning('⚠️ فشل إرسال النسخة الاحتياطية إلى تيليجرام')
                except Exception as e:
                    logging.error(f'❌ خطأ في النسخ الاحتياطي التلقائي: {str(e)}')
                    import traceback
                    traceback.print_exc()
            
            thread = threading.Thread(target=auto_backup)
            thread.daemon = True
            thread.start()
            logging.info('🚀 تم تشغيل thread النسخ الاحتياطي')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
    
    from app.models import user
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            if ':' in str(user_id):
                uid, session_version = str(user_id).split(':', 1)
                loaded_user = user.User.query.get(int(uid))
                if loaded_user and loaded_user.session_version == session_version and loaded_user.is_active:
                    return loaded_user
                return None
            else:
                loaded_user = user.User.query.get(int(user_id))
                if loaded_user and loaded_user.is_active:
                    return loaded_user
                return None
        except:
            return None
    
    from app.routes import auth, admin, public, teacher, student
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(public.bp)
    app.register_blueprint(teacher.bp)
    app.register_blueprint(student.bp)
    
    with app.app_context():
        db.create_all()
        from app.utils import init_db
        init_db.initialize_database()
    
    setup_auto_backup()
    
    from app.utils.scheduler import init_scheduler
    init_scheduler(app)
    
    return app
