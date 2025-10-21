from app import db
from datetime import datetime

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    course_name = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255))
    rating = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Testimonial {self.student_name}>'
