from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from sqlalchemy import event
import threading

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
    
    @event.listens_for(db.session, 'after_commit')
    def receive_after_commit(session):
        nonlocal modified_tables
        
        if modified_tables:
            print(f'تم تعديل الجداول التالية: {", ".join(modified_tables)}')
            tables_copy = modified_tables.copy()
            modified_tables.clear()
            
            def auto_backup():
                try:
                    from app.utils.backup import BackupManager
                    BackupManager.create_and_send_telegram_backup()
                except Exception as e:
                    print(f'خطأ في النسخ الاحتياطي التلقائي: {str(e)}')
                    import traceback
                    traceback.print_exc()
            
            thread = threading.Thread(target=auto_backup)
            thread.daemon = True
            thread.start()

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
        return user.User.query.get(int(user_id))
    
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
    
    return app
