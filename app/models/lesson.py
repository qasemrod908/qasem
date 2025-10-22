from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    file_type = db.Column(db.String(10))
    upload_date = db.Column(db.DateTime, default=damascus_now)
    is_published = db.Column(db.Boolean, default=True)
    
    teacher = db.relationship('Teacher', backref='lessons')
    
    def __repr__(self):
        return f'<Lesson {self.title}>'
