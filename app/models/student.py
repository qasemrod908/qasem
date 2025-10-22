from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_number = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    photo = db.Column(db.String(255))
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    user = db.relationship('User', backref='student_profile', foreign_keys=[user_id])
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    grades = db.relationship('Grade', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.student_number}>'
