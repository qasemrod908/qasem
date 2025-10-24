from app import db
from datetime import datetime
from app.utils.helpers import damascus_now

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=damascus_now)
    updated_at = db.Column(db.DateTime, default=damascus_now, onupdate=damascus_now)
    
    student = db.relationship('Student', backref='payments')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    installments = db.relationship('InstallmentPayment', backref='payment', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_paid(self):
        return self.paid_amount >= self.total_amount
    
    @property
    def is_partially_paid(self):
        return self.paid_amount > 0 and self.paid_amount < self.total_amount
    
    def update_status(self):
        if self.is_paid:
            self.status = 'paid'
        elif self.is_partially_paid:
            self.status = 'partial'
        else:
            self.status = 'pending'
        db.session.commit()
    
    def __repr__(self):
        return f'<Payment {self.title} - {self.student_id}>'


class InstallmentPayment(db.Model):
    __tablename__ = 'installment_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    receipt_number = db.Column(db.String(100))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=damascus_now)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f'<InstallmentPayment {self.amount} - Payment {self.payment_id}>'
