from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=damascus_now)
    send_telegram = db.Column(db.Boolean, default=True)
    send_web = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    
    creator = db.relationship('User', backref='created_notifications')
    recipients = db.relationship('NotificationRecipient', backref='notification', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Notification {self.title}>'
    
    def get_unread_count(self):
        return NotificationRecipient.query.filter_by(
            notification_id=self.id,
            is_read=False
        ).count()
    
    def get_delivery_stats(self):
        total = NotificationRecipient.query.filter_by(notification_id=self.id).count()
        delivered_telegram = NotificationRecipient.query.filter_by(
            notification_id=self.id,
            telegram_delivered=True
        ).count()
        delivered_web = NotificationRecipient.query.filter_by(
            notification_id=self.id,
            web_delivered=True
        ).count()
        read_count = NotificationRecipient.query.filter_by(
            notification_id=self.id,
            is_read=True
        ).count()
        
        return {
            'total': total,
            'delivered_telegram': delivered_telegram,
            'delivered_web': delivered_web,
            'read': read_count,
            'unread': total - read_count,
            'delivery_rate_telegram': (delivered_telegram / total * 100) if total > 0 else 0,
            'delivery_rate_web': (delivered_web / total * 100) if total > 0 else 0,
            'read_rate': (read_count / total * 100) if total > 0 else 0
        }


class NotificationRecipient(db.Model):
    __tablename__ = 'notification_recipients'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    telegram_delivered = db.Column(db.Boolean, default=False)
    telegram_delivered_at = db.Column(db.DateTime, nullable=True)
    web_delivered = db.Column(db.Boolean, default=False)
    web_delivered_at = db.Column(db.DateTime, nullable=True)
    telegram_message_id = db.Column(db.Integer, nullable=True)
    
    user = db.relationship('User', backref='notification_recipients')
    
    def __repr__(self):
        return f'<NotificationRecipient {self.id}>'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = damascus_now()
            db.session.commit()
    
    def mark_telegram_delivered(self, message_id=None):
        self.telegram_delivered = True
        self.telegram_delivered_at = damascus_now()
        if message_id:
            self.telegram_message_id = message_id
        db.session.commit()
    
    def mark_web_delivered(self):
        self.web_delivered = True
        self.web_delivered_at = damascus_now()
        db.session.commit()
