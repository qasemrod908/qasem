#!/usr/bin/env python3
"""
Script to update the database with the new attendance table unique constraint
"""
from main import app, db
from app.models.attendance import Attendance

def update_database():
    with app.app_context():
        print("تحديث قاعدة البيانات...")
        
        # Create the attendance table with the new constraint
        db.create_all()
        
        print("✓ تم تحديث قاعدة البيانات بنجاح")
        print("✓ تم إضافة القيد: قيد فريد على (user_id, date) لمنع التسجيلات المكررة")

if __name__ == '__main__':
    update_database()
