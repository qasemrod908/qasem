from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=damascus_now)
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    user = db.relationship('User', backref='attendance_records', foreign_keys=[user_id])
    
    __table_args__ = (
        db.Index('idx_attendance_user_date', 'user_id', 'date'),
        db.Index('idx_attendance_type_date', 'user_type', 'date'),
    )
    
    @staticmethod
    def get_user_stats(user_id, start_date=None, end_date=None):
        query = Attendance.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        records = query.all()
        total = len(records)
        present = sum(1 for r in records if r.status == 'present')
        absent = sum(1 for r in records if r.status == 'absent')
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'attendance_rate': round((present / total * 100) if total > 0 else 0, 2)
        }
    
    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date} - {self.status}>'
