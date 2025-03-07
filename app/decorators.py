from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def module_permission_required(module_code):
    """
    检查用户是否有权限访问指定模块的装饰器
    :param module_code: 模块代码
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否登录
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
                
            # 检查用户是否有权限访问该模块
            if not current_user.has_module_permission(module_code):
                flash('您没有权限访问此模块')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 