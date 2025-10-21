from app import db
from app.models import User, SiteSettings
from werkzeug.security import generate_password_hash

def initialize_database():
    admin_user = User.query.filter_by(email='admin@alqasim.edu').first()
    
    if not admin_user:
        admin = User(
            email='admin@alqasim.edu',
            full_name='المدير العام',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        settings = SiteSettings.query.first()
        if not settings:
            default_settings = SiteSettings(
                institute_name='معهد القاسم للعلوم واللغات',
                about_title='نبذة عن المعهد',
                about_content='معهد القاسم للعلوم واللغات مؤسسة تعليمية رائدة تقدم أفضل البرامج التعليمية',
                founding_date='2020',
                mission_statement='نسعى لتقديم تعليم متميز يساهم في بناء جيل واعٍ ومثقف',
                phone1='07XX-XXX-XXXX',
                email='info@alqasim.edu'
            )
            db.session.add(default_settings)
        
        db.session.commit()
        print('✅ تم إنشاء المستخدم الإداري الافتراضي')
        print('   البريد الإلكتروني: admin@alqasim.edu')
        print('   ⚠️  يرجى تغيير كلمة المرور الافتراضية فوراً من لوحة التحكم')
