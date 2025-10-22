from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    issued_date = db.Column(db.Date)
    is_published = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    def __repr__(self):
        return f'<Certificate {self.title}>'
