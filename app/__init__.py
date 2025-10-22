from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from sqlalchemy import event
import threading

db = SQLAlchemy()
login_manager = LoginManager()

def setup_auto_backup():
    @event.listens_for(db.session, 'after_commit')
    def receive_after_commit(session):
        def auto_backup():
            try:
                from app.utils.backup import BackupManager
                BackupManager.create_auto_backup()
            except Exception as e:
                print(f'خطأ في النسخ الاحتياطي التلقائي: {str(e)}')
        
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
