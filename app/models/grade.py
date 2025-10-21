from app import db
from datetime import datetime

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    max_grade = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    exam_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    course = db.relationship('Course', backref='grades')
    teacher = db.relationship('Teacher', backref='grades')
    
    def __repr__(self):
        return f'<Grade {self.exam_name}>'
