from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class News(db.Model):
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=damascus_now)
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    author = db.relationship('User', backref='news_articles')
    
    def __repr__(self):
        return f'<News {self.title}>'
