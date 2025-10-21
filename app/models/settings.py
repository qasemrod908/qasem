from app import db
from datetime import datetime

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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteSettings {self.institute_name}>'
