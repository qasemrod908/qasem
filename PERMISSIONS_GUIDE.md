# دليل نظام الصلاحيات الشامل - معهد القاسم

## نظرة عامة

تم تطوير نظام صلاحيات شامل ومتقدم يمكّن المدير الرئيسي من التحكم الكامل في صلاحيات جميع المستخدمين في النظام.

## المزايا الرئيسية

### 1. **صلاحيات مفصلة**
- كل ميزة في النظام لها صلاحيات محددة (عرض، إضافة، تعديل، حذف)
- أكثر من 80 صلاحية مختلفة موزعة على 17 فئة

### 2. **إدارة مرنة**
- واجهة مرئية سهلة الاستخدام لإدارة الصلاحيات
- إمكانية منح/إلغاء صلاحيات محددة لكل مستخدم
- نسخ الصلاحيات من مستخدم لآخر
- إعادة تعيين الصلاحيات الافتراضية

### 3. **صلاحيات افتراضية حسب الدور**
- كل دور (معاون، مدرس، طالب) له صلاحيات افتراضية مناسبة
- يتم تطبيق الصلاحيات الافتراضية تلقائياً عند إنشاء مستخدم جديد

## فئات الصلاحيات

### إدارة المستخدمين (users)
- `users.view` - عرض المستخدمين
- `users.add` - إضافة مستخدم
- `users.edit` - تعديل مستخدم
- `users.delete` - حذف مستخدم
- `users.manage_permissions` - إدارة صلاحيات المستخدمين
- `users.change_password` - تغيير كلمات المرور
- `users.toggle_status` - تفعيل/تعطيل المستخدمين

### إدارة الطلاب (students)
- `students.view` - عرض الطلاب
- `students.add` - إضافة طالب
- `students.edit` - تعديل طالب
- `students.delete` - حذف طالب
- `students.view_profile` - عرض الملف الشخصي للطالب
- `students.export` - تصدير بيانات الطلاب

### إدارة الأساتذة (teachers)
- `teachers.view` - عرض الأساتذة
- `teachers.add` - إضافة أستاذ
- `teachers.edit` - تعديل أستاذ
- `teachers.delete` - حذف أستاذ
- `teachers.view_profile` - عرض الملف الشخصي للأستاذ
- `teachers.export` - تصدير بيانات الأساتذة

### إدارة الدورات (courses)
- `courses.view` - عرض الدورات
- `courses.add` - إضافة دورة
- `courses.edit` - تعديل دورة
- `courses.delete` - حذف دورة
- `courses.upload_image` - رفع صور الدورات

### إدارة الدروس (lessons)
- `lessons.view` - عرض الدروس
- `lessons.add` - إضافة درس
- `lessons.edit` - تعديل درس
- `lessons.delete` - حذف درس
- `lessons.upload_file` - رفع ملفات الدروس
- `lessons.publish` - نشر/إخفاء الدروس

### إدارة التسجيلات (enrollments)
- `enrollments.view` - عرض التسجيلات
- `enrollments.add` - تسجيل طالب في دورة
- `enrollments.edit` - تعديل تسجيل
- `enrollments.delete` - حذف تسجيل
- `enrollments.assign_teacher` - تعيين أستاذ للطالب

### إدارة العلامات (grades)
- `grades.view` - عرض العلامات
- `grades.view_all` - عرض جميع العلامات
- `grades.add` - إضافة علامة
- `grades.edit` - تعديل علامة
- `grades.delete` - حذف علامة
- `grades.export` - تصدير العلامات

### إدارة الأقساط والدفعات (payments)
- `payments.view` - عرض الأقساط
- `payments.view_all` - عرض جميع الأقساط
- `payments.add` - إضافة قسط
- `payments.edit` - تعديل قسط
- `payments.delete` - حذف قسط
- `payments.add_installment` - إضافة دفعة
- `payments.edit_installment` - تعديل دفعة
- `payments.delete_installment` - حذف دفعة
- `payments.export` - تصدير الأقساط
- `payments.view_reports` - عرض التقارير المالية

### إدارة الحضور والغياب (attendance)
- `attendance.view` - عرض سجلات الحضور
- `attendance.add` - تسجيل حضور
- `attendance.edit` - تعديل سجل حضور
- `attendance.delete` - حذف سجل حضور
- `attendance.bulk_add` - تسجيل حضور جماعي
- `attendance.export` - تصدير سجلات الحضور
- `attendance.view_reports` - عرض تقارير الحضور

### إدارة الإشعارات (notifications)
- `notifications.view` - عرض الإشعارات
- `notifications.create` - إنشاء إشعار
- `notifications.edit` - تعديل إشعار
- `notifications.delete` - حذف إشعار
- `notifications.send` - إرسال إشعارات
- `notifications.bulk_actions` - إجراءات جماعية

وفئات إضافية لـ: الأخبار، الصفوف والشعب، الرسائل، الإعدادات، النسخ الاحتياطي، تصفير البيانات، بوت تليجرام، والتقارير.

## كيفية استخدام نظام الصلاحيات

### للمدير الرئيسي

1. **الوصول إلى إدارة الصلاحيات:**
   - انتقل إلى "إدارة المستخدمين"
   - اضغط على زر "إدارة الصلاحيات"

2. **تعديل صلاحيات مستخدم:**
   - اختر المستخدم من القائمة
   - اضغط على "إدارة الصلاحيات"
   - حدد/ألغِ تحديد الصلاحيات المطلوبة
   - احفظ التغييرات

3. **نسخ الصلاحيات:**
   - في صفحة تعديل الصلاحيات
   - اضغط على "نسخ صلاحيات من مستخدم آخر"
   - اختر المستخدم المصدر
   - سيتم نسخ جميع صلاحياته

4. **إعادة تعيين الصلاحيات:**
   - اضغط على "إعادة تعيين الصلاحيات الافتراضية"
   - سيتم استعادة الصلاحيات الافتراضية للدور

### للمطورين

#### استخدام decorators الصلاحيات

```python
from app.utils.decorators import (
    permission_required,
    any_permission_required,
    all_permissions_required,
    role_or_permission_required
)

# يتطلب صلاحية واحدة
@bp.route('/students')
@permission_required('students.view')
def students():
    pass

# يتطلب أي صلاحية من المحددة
@bp.route('/data')
@any_permission_required('students.view', 'teachers.view')
def view_data():
    pass

# يتطلب جميع الصلاحيات المحددة
@bp.route('/advanced')
@all_permissions_required('students.edit', 'students.delete')
def advanced_action():
    pass

# يتطلب دور معين أو صلاحيات معينة
@bp.route('/courses')
@role_or_permission_required(
    roles=['admin', 'assistant'],
    permissions=['courses.view']
)
def courses():
    pass
```

#### التحقق من الصلاحيات في الكود

```python
from flask_login import current_user

# التحقق من صلاحية واحدة
if current_user.has_permission('students.edit'):
    # السماح بالتعديل
    pass

# التحقق من صلاحيات متعددة
if current_user.has_permission('payments.view') and current_user.has_permission('payments.edit'):
    # السماح بالعرض والتعديل
    pass
```

## الصلاحيات الافتراضية

### المعاون (assistant)
- جميع صلاحيات العرض والإضافة والتعديل للطلاب والأساتذة
- إدارة التسجيلات والعلامات
- إدارة الأقساط والحضور
- عرض الإشعارات والتقارير

### المدرس (teacher)
- عرض الطلاب وملفاتهم الشخصية
- إدارة الدروس (إضافة، تعديل، رفع ملفات)
- إدارة العلامات (عرض، إضافة، تعديل)
- تسجيل الحضور
- عرض الإشعارات

### الطالب (student)
- عرض الدورات والدروس
- عرض العلامات والأقساط
- عرض الحضور والإشعارات

## ملاحظات مهمة

1. **المدير الرئيسي (admin):**
   - لديه جميع الصلاحيات تلقائياً بدون قيود
   - لا يمكن تعديل صلاحياته من واجهة الإدارة

2. **أمان النظام:**
   - جميع الـ routes محمية بنظام الصلاحيات
   - المستخدمون بدون صلاحية مناسبة لا يمكنهم الوصول

3. **المرونة:**
   - يمكن تخصيص الصلاحيات لكل مستخدم على حدة
   - يمكن منح مستخدم صلاحيات أكثر أو أقل من الافتراضية

## تطبيق الصلاحيات على المستخدمين الحاليين

إذا كنت تقوم بترقية نظام موجود، قم بتشغيل السكريبت التالي مرة واحدة:

```bash
python apply_default_permissions.py
```

هذا السكريبت سيقوم بـ:
- تطبيق الصلاحيات الافتراضية على جميع المستخدمين الحاليين
- تخطي المستخدمين الذين لديهم صلاحيات مخصصة بالفعل
- تخطي المدراء الرئيسيين

## الملفات المتعلقة بنظام الصلاحيات

- `app/utils/permissions_config.py` - تعريف جميع الصلاحيات وإعداداتها
- `app/utils/decorators.py` - decorators للتحقق من الصلاحيات
- `app/routes/admin.py` - routes إدارة الصلاحيات
- `app/templates/admin/manage_permissions.html` - واجهة عرض المستخدمين
- `app/templates/admin/edit_permissions.html` - واجهة تعديل الصلاحيات
- `app/models/user.py` - نموذج المستخدم مع حقل permissions
- `apply_default_permissions.py` - سكريبت تطبيق الصلاحيات الافتراضية
