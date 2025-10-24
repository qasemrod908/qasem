from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    institute_name = db.Column(db.String(200), default='معهد القاسم للعلوم واللغات')
    logo = db.Column(db.String(255))
    about_title = db.Column(db.String(200))
    about_content = db.Column(db.Text)
    founding_date = db.Column(db.String(100))
    mission_statement = db.Column(db.Text)
    facebook_url = db.Column(db.String(255))
    phone1 = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    telegram_bot_token = db.Column(db.String(255))
    telegram_chat_id = db.Column(db.String(100))
    telegram_backup_enabled = db.Column(db.Boolean, default=False)
    
    telegram_bot_enabled = db.Column(db.Boolean, default=False)
    telegram_bot_webhook_enabled = db.Column(db.Boolean, default=False)
    telegram_bot_webhook_url = db.Column(db.String(500))
    telegram_bot_notifications_enabled = db.Column(db.Boolean, default=True)
    
    courses_slider_items = db.Column(db.Integer, default=3)
    courses_slider_interval = db.Column(db.Integer, default=5000)
    courses_slider_auto_play = db.Column(db.Boolean, default=True)
    courses_slider_transition = db.Column(db.String(20), default='slide')
    
    teachers_slider_items = db.Column(db.Integer, default=4)
    teachers_slider_interval = db.Column(db.Integer, default=5000)
    teachers_slider_auto_play = db.Column(db.Boolean, default=True)
    teachers_slider_transition = db.Column(db.String(20), default='slide')
    
    payment_reminder_enabled = db.Column(db.Boolean, default=True)
    payment_reminder_days_before = db.Column(db.Integer, default=3)
    payment_reminder_time = db.Column(db.String(5), default='09:00')
    payment_reminder_message = db.Column(db.Text, default='تذكير: لديك قسط مستحق\n\n📋 العنوان: {title}\n💰 المبلغ الإجمالي: {total_amount} ل.س\n💳 المبلغ المدفوع: {paid_amount} ل.س\n📊 المبلغ المتبقي: {remaining_amount} ل.س\n📅 تاريخ الاستحقاق: {due_date}\n\nيرجى تسديد المبلغ المتبقي في أقرب وقت ممكن.')
    
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    def __repr__(self):
        return f'<SiteSettings {self.institute_name}>'
