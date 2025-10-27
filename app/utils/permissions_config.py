# نظام الصلاحيات الشامل - معهد القاسم

PERMISSIONS_STRUCTURE = {
    'users': {
        'name': 'إدارة المستخدمين',
        'permissions': {
            'users.view': 'عرض المستخدمين',
            'users.add': 'إضافة مستخدم',
            'users.edit': 'تعديل مستخدم',
            'users.delete': 'حذف مستخدم',
            'users.manage_permissions': 'إدارة صلاحيات المستخدمين',
            'users.change_password': 'تغيير كلمات المرور',
            'users.toggle_status': 'تفعيل/تعطيل المستخدمين'
        }
    },
    
    'students': {
        'name': 'إدارة الطلاب',
        'permissions': {
            'students.view': 'عرض الطلاب',
            'students.add': 'إضافة طالب',
            'students.edit': 'تعديل طالب',
            'students.delete': 'حذف طالب',
            'students.view_profile': 'عرض الملف الشخصي للطالب',
            'students.export': 'تصدير بيانات الطلاب'
        }
    },
    
    'teachers': {
        'name': 'إدارة الأساتذة',
        'permissions': {
            'teachers.view': 'عرض الأساتذة',
            'teachers.add': 'إضافة أستاذ',
            'teachers.edit': 'تعديل أستاذ',
            'teachers.delete': 'حذف أستاذ',
            'teachers.view_profile': 'عرض الملف الشخصي للأستاذ',
            'teachers.export': 'تصدير بيانات الأساتذة'
        }
    },
    
    'courses': {
        'name': 'إدارة الدورات',
        'permissions': {
            'courses.view': 'عرض الدورات',
            'courses.add': 'إضافة دورة',
            'courses.edit': 'تعديل دورة',
            'courses.delete': 'حذف دورة',
            'courses.upload_image': 'رفع صور الدورات'
        }
    },
    
    'lessons': {
        'name': 'إدارة الدروس',
        'permissions': {
            'lessons.view': 'عرض الدروس',
            'lessons.add': 'إضافة درس',
            'lessons.edit': 'تعديل درس',
            'lessons.delete': 'حذف درس',
            'lessons.upload_file': 'رفع ملفات الدروس',
            'lessons.publish': 'نشر/إخفاء الدروس'
        }
    },
    
    'enrollments': {
        'name': 'إدارة التسجيلات',
        'permissions': {
            'enrollments.view': 'عرض التسجيلات',
            'enrollments.add': 'تسجيل طالب في دورة',
            'enrollments.edit': 'تعديل تسجيل',
            'enrollments.delete': 'حذف تسجيل',
            'enrollments.assign_teacher': 'تعيين أستاذ للطالب'
        }
    },
    
    'grades': {
        'name': 'إدارة العلامات',
        'permissions': {
            'grades.view': 'عرض العلامات',
            'grades.view_all': 'عرض جميع العلامات',
            'grades.add': 'إضافة علامة',
            'grades.edit': 'تعديل علامة',
            'grades.delete': 'حذف علامة',
            'grades.export': 'تصدير العلامات'
        }
    },
    
    'payments': {
        'name': 'إدارة الأقساط والدفعات',
        'permissions': {
            'payments.view': 'عرض الأقساط',
            'payments.view_all': 'عرض جميع الأقساط',
            'payments.add': 'إضافة قسط',
            'payments.edit': 'تعديل قسط',
            'payments.delete': 'حذف قسط',
            'payments.add_installment': 'إضافة دفعة',
            'payments.edit_installment': 'تعديل دفعة',
            'payments.delete_installment': 'حذف دفعة',
            'payments.export': 'تصدير الأقساط',
            'payments.view_reports': 'عرض التقارير المالية'
        }
    },
    
    'attendance': {
        'name': 'إدارة الحضور والغياب',
        'permissions': {
            'attendance.view': 'عرض سجلات الحضور',
            'attendance.add': 'تسجيل حضور',
            'attendance.edit': 'تعديل سجل حضور',
            'attendance.delete': 'حذف سجل حضور',
            'attendance.bulk_add': 'تسجيل حضور جماعي',
            'attendance.export': 'تصدير سجلات الحضور',
            'attendance.view_reports': 'عرض تقارير الحضور'
        }
    },
    
    'notifications': {
        'name': 'إدارة الإشعارات',
        'permissions': {
            'notifications.view': 'عرض الإشعارات',
            'notifications.create': 'إنشاء إشعار',
            'notifications.edit': 'تعديل إشعار',
            'notifications.delete': 'حذف إشعار',
            'notifications.send': 'إرسال إشعارات',
            'notifications.bulk_actions': 'إجراءات جماعية'
        }
    },
    
    'news': {
        'name': 'إدارة الأخبار',
        'permissions': {
            'news.view': 'عرض الأخبار',
            'news.add': 'إضافة خبر',
            'news.edit': 'تعديل خبر',
            'news.delete': 'حذف خبر',
            'news.upload_image': 'رفع صور الأخبار'
        }
    },
    
    'classes': {
        'name': 'إدارة الصفوف والشعب',
        'permissions': {
            'classes.view': 'عرض الصفوف والشعب',
            'classes.add': 'إضافة صف/شعبة',
            'classes.edit': 'تعديل صف/شعبة',
            'classes.delete': 'حذف صف/شعبة',
            'classes.view_stats': 'عرض إحصائيات الصفوف'
        }
    },
    
    'contacts': {
        'name': 'إدارة الرسائل',
        'permissions': {
            'contacts.view': 'عرض الرسائل',
            'contacts.delete': 'حذف رسالة',
            'contacts.mark_read': 'تعليم كمقروءة',
            'contacts.export': 'تصدير الرسائل'
        }
    },
    
    'settings': {
        'name': 'إدارة الإعدادات',
        'permissions': {
            'settings.view': 'عرض الإعدادات',
            'settings.edit': 'تعديل الإعدادات',
            'settings.upload_logo': 'رفع شعار المعهد',
            'settings.telegram': 'إعدادات تليجرام',
            'settings.slider': 'إعدادات السلايدر',
            'settings.payment_reminders': 'إعدادات تذكير الأقساط'
        }
    },
    
    'backup': {
        'name': 'النسخ الاحتياطي والاستعادة',
        'permissions': {
            'backup.view': 'عرض النسخ الاحتياطية',
            'backup.create': 'إنشاء نسخة احتياطية',
            'backup.download': 'تحميل نسخة احتياطية',
            'backup.restore': 'استعادة نسخة احتياطية',
            'backup.delete': 'حذف نسخة احتياطية'
        }
    },
    
    'data_reset': {
        'name': 'تصفير البيانات',
        'permissions': {
            'data_reset.view': 'عرض صفحة التصفير',
            'data_reset.execute': 'تنفيذ عملية التصفير'
        }
    },
    
    'bot': {
        'name': 'إدارة بوت تليجرام',
        'permissions': {
            'bot.view': 'عرض إحصائيات البوت',
            'bot.manage': 'إدارة البوت',
            'bot.start_stop': 'تشغيل/إيقاف البوت'
        }
    },
    
    'reports': {
        'name': 'التقارير والإحصائيات',
        'permissions': {
            'reports.dashboard': 'عرض لوحة التحكم',
            'reports.financial': 'التقارير المالية',
            'reports.academic': 'التقارير الأكاديمية',
            'reports.attendance': 'تقارير الحضور'
        }
    }
}


# الحصول على جميع الصلاحيات كقائمة مسطحة
def get_all_permissions():
    """الحصول على جميع الصلاحيات كقاموس مسطح"""
    all_perms = {}
    for category_key, category_data in PERMISSIONS_STRUCTURE.items():
        all_perms.update(category_data['permissions'])
    return all_perms


# الحصول على الصلاحيات حسب الفئة
def get_permissions_by_category():
    """الحصول على الصلاحيات مرتبة حسب الفئات"""
    return PERMISSIONS_STRUCTURE


# الحصول على جميع مفاتيح الصلاحيات
def get_all_permission_keys():
    """الحصول على جميع مفاتيح الصلاحيات كقائمة"""
    keys = []
    for category_data in PERMISSIONS_STRUCTURE.values():
        keys.extend(category_data['permissions'].keys())
    return keys


# التحقق من وجود صلاحية
def is_valid_permission(permission_key):
    """التحقق من وجود صلاحية معينة"""
    return permission_key in get_all_permission_keys()


# الحصول على وصف الصلاحية
def get_permission_description(permission_key):
    """الحصول على الوصف النصي للصلاحية"""
    all_perms = get_all_permissions()
    return all_perms.get(permission_key, 'غير معروف')


# الحصول على اسم الفئة للصلاحية
def get_permission_category(permission_key):
    """الحصول على اسم الفئة التي تنتمي إليها الصلاحية"""
    for category_key, category_data in PERMISSIONS_STRUCTURE.items():
        if permission_key in category_data['permissions']:
            return category_data['name']
    return 'غير معروف'


# الصلاحيات الافتراضية حسب الدور
DEFAULT_PERMISSIONS = {
    'admin': [],  # المدير لديه جميع الصلاحيات تلقائياً
    
    'assistant': [
        'students.view', 'students.add', 'students.edit',
        'teachers.view',
        'courses.view',
        'lessons.view',
        'enrollments.view', 'enrollments.add', 'enrollments.edit', 'enrollments.assign_teacher',
        'grades.view_all', 'grades.add', 'grades.edit',
        'payments.view_all', 'payments.add', 'payments.edit', 'payments.add_installment',
        'attendance.view', 'attendance.add', 'attendance.edit', 'attendance.bulk_add',
        'notifications.view', 'notifications.create',
        'news.view',
        'classes.view', 'classes.view_stats',
        'contacts.view',
        'reports.dashboard', 'reports.financial', 'reports.academic', 'reports.attendance'
    ],
    
    'teacher': [
        'students.view', 'students.view_profile',
        'lessons.view', 'lessons.add', 'lessons.edit', 'lessons.upload_file', 'lessons.publish',
        'grades.view', 'grades.add', 'grades.edit',
        'attendance.view', 'attendance.add',
        'notifications.view'
    ],
    
    'student': [
        'courses.view',
        'lessons.view',
        'grades.view',
        'payments.view',
        'attendance.view',
        'notifications.view'
    ]
}


def get_default_permissions_for_role(role):
    """الحصول على الصلاحيات الافتراضية لدور معين"""
    return DEFAULT_PERMISSIONS.get(role, [])


# وظيفة لتطبيق الصلاحيات الافتراضية على مستخدم جديد
def apply_default_permissions(user):
    """تطبيق الصلاحيات الافتراضية على مستخدم"""
    if user.role == 'admin':
        user.permissions = {}  # المدير لديه جميع الصلاحيات
    else:
        default_perms = get_default_permissions_for_role(user.role)
        user.permissions = {perm: True for perm in default_perms}
    return user
