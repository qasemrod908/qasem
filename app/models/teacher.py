from app import db
from datetime import datetime

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    specialization = db.Column(db.String(100))
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    qualifications = db.Column(db.Text)
    photo = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='teacher_profile', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Teacher {self.user.full_name}>'
