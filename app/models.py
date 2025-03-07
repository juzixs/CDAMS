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
    vehicle_type = db.Column(db.String(20), nullable=False)  # 燃油/新能源
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
    background_image = db.Column(db.String(200))  # 背景图路径
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

class Dormitory(db.Model):
    """宿舍模型"""
    __tablename__ = 'dormitories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 宿舍名称
    address = db.Column(db.String(200))  # 宿舍地址
    type = db.Column(db.String(20))  # 自有/租赁
    lease_start_date = db.Column(db.Date)  # 租赁开始日期
    lease_end_date = db.Column(db.Date)  # 租赁结束日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与房间的关系
    rooms = db.relationship('Room', backref='dormitory', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Dormitory {self.name}>'


class Room(db.Model):
    """房间模型"""
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey('dormitory.id'), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)  # 男生宿舍/女生宿舍/高管间/访客间
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'))  # 宿舍长ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    building = db.relationship('Dormitory', backref='rooms')
    students = db.relationship('Monitor', backref='room', foreign_keys='Monitor.room_id')
    monitor = db.relationship('Monitor', foreign_keys=[monitor_id])  # 宿舍长关系

    @property
    def can_have_monitor(self):
        """判断是否可以设置宿舍长"""
        return self.room_type in ['男生宿舍', '女生宿舍']

    def __repr__(self):
        return f'<Room {self.room_number}>'
    
    @property
    def current_residents_count(self):
        """获取当前入住人数"""
        return self.residents.filter(Resident.checkout_date.is_(None)).count()
    
    @property
    def is_full(self):
        """判断房间是否已满"""
        return self.current_residents_count >= self.capacity


class Resident(db.Model):
    """住户模型"""
    __tablename__ = 'residents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 姓名
    gender = db.Column(db.String(10), nullable=False)  # 性别
    department = db.Column(db.String(100))  # 部门
    position = db.Column(db.String(100))  # 岗位
    phone = db.Column(db.String(20))  # 手机
    remarks = db.Column(db.Text)  # 备注
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    checkin_date = db.Column(db.DateTime, default=datetime.utcnow)  # 入住时间
    checkout_date = db.Column(db.DateTime)  # 退住时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Resident {self.name}>' 

class Monitor(db.Model):
    """宿舍长模型"""
    __tablename__ = 'monitors'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # 员工编号
    name = db.Column(db.String(100), nullable=False)  # 姓名
    gender = db.Column(db.String(10), nullable=False)  # 性别
    department = db.Column(db.String(100))  # 部门
    position = db.Column(db.String(100))  # 岗位
    phone = db.Column(db.String(20))  # 手机
    email = db.Column(db.String(120))  # 邮箱
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))  # 房间ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Monitor {self.name}>' 
