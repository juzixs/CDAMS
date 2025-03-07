from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

# 用户模块权限关联表
user_module_permissions = db.Table('user_module_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('module_id', db.Integer, db.ForeignKey('modules.id'), primary_key=True)
)

class Module(db.Model):
    """系统模块"""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    permission_level = db.Column(db.String(20), default='authorized')  # normal, authorized, admin
    
    def __repr__(self):
        return f'<Module {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(64), nullable=True)
    department = db.Column(db.String(64), nullable=True)
    position = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    authorized_modules = db.relationship('Module', 
                                        secondary=user_module_permissions,
                                        lazy='subquery',
                                        backref=db.backref('authorized_users', lazy=True))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_module_permission(self, module_code):
        """检查用户是否有权限访问指定模块"""
        # 管理员可以访问所有模块
        if self.is_admin:
            return True
            
        # 获取模块信息
        module = Module.query.filter_by(code=module_code).first()
        if not module:
            return False
            
        # 普通级别模块所有人可访问
        if module.permission_level == 'normal':
            return True
            
        # 授权级别模块需要特定授权
        if module.permission_level == 'authorized':
            return module in self.authorized_modules
            
        # 管理级别模块只有管理员可访问
        if module.permission_level == 'admin':
            return self.is_admin
            
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
