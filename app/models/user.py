from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.utils.helpers import damascus_now

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    permissions = db.Column(db.JSON, default={})
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        if self.role == 'admin':
            return True
        return self.permissions.get(permission, False)
    
    def get_unread_notifications_count(self):
        from app.models.notification import NotificationRecipient, Notification
        return NotificationRecipient.query.filter_by(
            user_id=self.id,
            is_read=False
        ).join(Notification).filter(Notification.is_active == True).count()
    
    def __repr__(self):
        return f'<User {self.phone_number}>'
