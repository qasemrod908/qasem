from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class BotSession(db.Model):
    __tablename__ = 'bot_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('bot_sessions', lazy='dynamic'))
    
    is_authenticated = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20))
    
    last_command = db.Column(db.String(50))
    conversation_state = db.Column(db.String(50))
    temp_data = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=damascus_now)
    last_activity = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    def __repr__(self):
        return f'<BotSession {self.telegram_id} - {self.username}>'
    
    def authenticate(self, user):
        self.user_id = user.id
        self.phone_number = user.phone_number
        self.is_authenticated = True
        db.session.commit()
    
    def logout(self):
        self.user_id = None
        self.is_authenticated = False
        self.conversation_state = None
        self.temp_data = None
        db.session.commit()

class BotStatistics(db.Model):
    __tablename__ = 'bot_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    total_users = db.Column(db.Integer, default=0)
    active_users_today = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    messages_received = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, default=damascus_now().date, unique=True)
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    def __repr__(self):
        return f'<BotStatistics {self.date}>'
