from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class ClassGrade(db.Model):
    __tablename__ = 'class_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    sections = db.relationship('Section', back_populates='class_grade', lazy='dynamic', cascade='all, delete-orphan')
    students = db.relationship('Student', back_populates='class_grade', lazy='dynamic')
    
    def __repr__(self):
        return f'<ClassGrade {self.name}>'

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_grade_id = db.Column(db.Integer, db.ForeignKey('class_grades.id'), nullable=False)
    description = db.Column(db.Text)
    max_students = db.Column(db.Integer)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    class_grade = db.relationship('ClassGrade', back_populates='sections')
    students = db.relationship('Student', back_populates='section', lazy='dynamic')
    
    __table_args__ = (db.UniqueConstraint('name', 'class_grade_id', name='unique_section_per_grade'),)
    
    def __repr__(self):
        return f'<Section {self.name} - {self.class_grade.name}>'
    
    def enrolled_count(self):
        """عدد الطلاب المسجلين في الشعبة"""
        return self.students.count()
    
    def available_seats(self):
        """عدد المقاعد المتاحة"""
        if self.max_students:
            return max(0, self.max_students - self.enrolled_count())
        return None
