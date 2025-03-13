from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """检查用户是否具有管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('您没有权限访问此页面', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function 