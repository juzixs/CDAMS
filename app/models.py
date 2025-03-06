from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    vehicles = db.relationship('Vehicle', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False)  # 燃油/新能�?
    owner_name = db.Column(db.String(64), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    remarks = db.Column(db.Text)  # 备注信息
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    issued_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'vehicle_type': self.vehicle_type,
            'owner_name': self.owner_name,
            'department': self.department,
            'remarks': self.remarks,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'issued_at': self.issued_at.strftime('%Y-%m-%d %H:%M:%S') if self.issued_at else None
        }

class PdfSettings(db.Model):
    """PDF生成设置"""
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), nullable=False)  # 模块名称
    background_image = db.Column(db.String(200))  # 背景图路�?
    font_family = db.Column(db.String(50))  # 字体
    font_size = db.Column(db.Integer)  # 字体大小
    font_bold = db.Column(db.Boolean, default=False)  # 是否加粗
    text_x = db.Column(db.Integer)  # 文字X坐标
    text_y = db.Column(db.Integer)  # 文字Y坐标
    text_color = db.Column(db.String(20))  # 文字颜色
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'module': self.module,
            'background_image': self.background_image,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_bold': self.font_bold,
            'text_x': self.text_x,
            'text_y': self.text_y,
            'text_color': self.text_color
        } 
