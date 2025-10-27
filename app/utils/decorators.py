from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission):
                flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def any_permission_required(*permissions):
    """يسمح بالوصول إذا كان لدى المستخدم أي صلاحية من الصلاحيات المحددة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            has_any = any(current_user.has_permission(perm) for perm in permissions)
            if not has_any:
                flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def all_permissions_required(*permissions):
    """يسمح بالوصول فقط إذا كان لدى المستخدم جميع الصلاحيات المحددة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            has_all = all(current_user.has_permission(perm) for perm in permissions)
            if not has_all:
                flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_or_permission_required(roles=None, permissions=None):
    """يسمح بالوصول إذا كان المستخدم لديه أحد الأدوار أو أي من الصلاحيات المحددة
    
    ملاحظة: المدير الرئيسي (super admin) له صلاحيات كاملة.
    المدراء العاديون يجب أن تكون لديهم الصلاحيات المحددة.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.is_super_admin():
                return f(*args, **kwargs)
            
            has_role = roles and current_user.role in roles and current_user.role != 'admin'
            has_permission = permissions and any(current_user.has_permission(perm) for perm in permissions)
            
            if not (has_role or has_permission):
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_permission(permission):
    """يتحقق من صلاحية محددة للمستخدم الحالي"""
    if not current_user.is_authenticated:
        return False
    return current_user.has_permission(permission)
