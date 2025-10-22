from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    duration = db.Column(db.String(100))
    level = db.Column(db.String(50))
    is_featured = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    max_students = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=damascus_now)
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def enrolled_count(self):
        """عدد الطلاب المسجلين"""
        return self.enrollments.filter_by(status='active').count()
    
    def available_seats(self):
        """عدد المقاعد المتاحة"""
        if self.max_students:
            return max(0, self.max_students - self.enrolled_count())
        return None
    
    def __repr__(self):
        return f'<Course {self.title}>'
