#!/usr/bin/env python3
"""
Migration script to add unique constraint on attendance table
This script properly handles existing databases
"""
from main import app, db
from sqlalchemy import text
import sys

def migrate_attendance_constraint():
    with app.app_context():
        try:
            print("التحقق من وجود قاعدة البيانات...")
            
            # Check if attendance table exists
            result = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'"
            ))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("جدول الحضور غير موجود. إنشاء الجداول...")
                db.create_all()
                print("✓ تم إنشاء جدول الحضور بنجاح مع القيد الفريد")
                return
            
            print("جدول الحضور موجود. التحقق من القيد الفريد...")
            
            # Check if unique constraint exists
            result = db.session.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='attendance'"
            ))
            table_sql = result.fetchone()
            
            if table_sql and 'uq_user_date' in table_sql[0]:
                print("⚠️  القيد الفريد موجود بالفعل")
                return
            
            print("إضافة القيد الفريد...")
            
            # For SQLite, we need to recreate the table with the constraint
            # Step 1: Drop existing indexes
            try:
                db.session.execute(text("DROP INDEX IF EXISTS idx_attendance_user_date"))
                db.session.execute(text("DROP INDEX IF EXISTS idx_attendance_type_date"))
            except:
                pass
            
            # Step 2: Rename old table
            db.session.execute(text("ALTER TABLE attendance RENAME TO attendance_old"))
            
            # Step 3: Create new table with constraint
            db.create_all()
            
            # Step 4: Copy data (removing duplicates, keeping the first record)
            db.session.execute(text("""
                INSERT INTO attendance (id, user_id, user_type, date, status, notes, created_at, updated_at)
                SELECT id, user_id, user_type, date, status, notes, created_at, updated_at
                FROM attendance_old
                WHERE id IN (
                    SELECT MIN(id)
                    FROM attendance_old
                    GROUP BY user_id, date
                )
            """))
            
            # Step 5: Drop old table
            db.session.execute(text("DROP TABLE attendance_old"))
            
            db.session.commit()
            
            print("✓ تم تطبيق القيد الفريد بنجاح")
            print("✓ تم حذف أي سجلات مكررة (تم الاحتفاظ بأول سجل لكل مستخدم/تاريخ)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ: {str(e)}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    migrate_attendance_constraint()
