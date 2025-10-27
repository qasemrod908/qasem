#!/usr/bin/env python3
"""
سكريبت لتطبيق الصلاحيات الافتراضية على جميع المستخدمين الموجودين في قاعدة البيانات
يستخدم هذا السكريبت مرة واحدة بعد تفعيل نظام الصلاحيات الجديد
"""

from app import create_app, db
from app.models import User
from app.utils.permissions_config import apply_default_permissions

def main():
    app = create_app()
    
    with app.app_context():
        print("بدء تطبيق الصلاحيات الافتراضية على المستخدمين...")
        print("-" * 50)
        
        users = User.query.all()
        updated_count = 0
        skipped_count = 0
        
        for user in users:
            if user.role == 'admin':
                print(f"⏩ تخطي {user.full_name} (مدير رئيسي)")
                skipped_count += 1
                continue
            
            if user.permissions is None or not user.permissions:
                apply_default_permissions(user)
                updated_count += 1
                perm_count = len(user.permissions.keys()) if user.permissions else 0
                print(f"✅ تم تطبيق {perm_count} صلاحية على {user.full_name} ({user.role})")
            else:
                print(f"⏩ {user.full_name} لديه صلاحيات مخصصة بالفعل - تخطي")
                skipped_count += 1
        
        try:
            db.session.commit()
            print("-" * 50)
            print(f"✅ تم بنجاح!")
            print(f"📊 الإحصائيات:")
            print(f"   - تم تحديث: {updated_count} مستخدم")
            print(f"   - تم التخطي: {skipped_count} مستخدم")
            print(f"   - الإجمالي: {len(users)} مستخدم")
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ أثناء الحفظ: {str(e)}")
            return 1
        
        return 0

if __name__ == '__main__':
    exit(main())
