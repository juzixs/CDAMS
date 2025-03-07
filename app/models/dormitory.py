from datetime import datetime
from app import db

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
    dormitory_id = db.Column(db.Integer, db.ForeignKey('dormitories.id'), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)  # 男工宿舍/女工宿舍/高管间/访客间
    capacity = db.Column(db.Integer, nullable=False)
    facilities = db.Column(db.String(500))  # 房间配置，如：空调,电视,独卫
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'))  # 宿舍长ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    residents = db.relationship('Resident', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    monitor = db.relationship('Monitor', foreign_keys=[monitor_id])  # 宿舍长关系

    @property
    def can_have_monitor(self):
        """判断是否可以设置宿舍长"""
        return self.room_type in ['男工宿舍', '女工宿舍']

    def __repr__(self):
        return f'<Room {self.room_number}>'
    
    @property
    def current_residents_count(self):
        """当前入住人数"""
        return self.residents.filter_by(checkout_date=None).count()
    
    @property
    def is_full(self):
        """房间是否已满"""
        return self.current_residents_count >= self.capacity


class Monitor(db.Model):
    """宿舍长模型"""
    __tablename__ = 'monitors'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # 工号
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