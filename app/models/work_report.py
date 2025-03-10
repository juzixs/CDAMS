from datetime import datetime
import json
from app.extensions import db
from flask_login import current_user

class WeeklyReport(db.Model):
    """周报模型"""
    __tablename__ = 'weekly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.DateTime)
    meeting_place = db.Column(db.String(100))
    host = db.Column(db.String(50))
    participants = db.Column(db.String(200))
    consensus = db.Column(db.Text)
    
    # 存储为JSON字符串
    _key_works = db.Column(db.Text)
    _temp_works = db.Column(db.Text)
    _coordinations = db.Column(db.Text)
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('weekly_reports', lazy='dynamic'))
    
    # 状态：draft-草稿, submitted-提交, archived-归档
    status = db.Column(db.String(20), default='draft')
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @property
    def key_works(self):
        if not self._key_works:
            return []
        return json.loads(self._key_works)
    
    @key_works.setter
    def key_works(self, value):
        self._key_works = json.dumps(value)
    
    @property
    def temp_works(self):
        if not self._temp_works:
            return []
        return json.loads(self._temp_works)
    
    @temp_works.setter
    def temp_works(self, value):
        self._temp_works = json.dumps(value)
    
    @property
    def coordinations(self):
        if not self._coordinations:
            return []
        return json.loads(self._coordinations)
    
    @coordinations.setter
    def coordinations(self, value):
        self._coordinations = json.dumps(value)
    
    def __repr__(self):
        return f'<WeeklyReport {self.week_number}>'

class MonthlyReport(db.Model):
    """月报模型"""
    __tablename__ = 'monthly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text)
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('monthly_reports', lazy='dynamic'))
    
    # 状态：draft-草稿, submitted-已提交, approved-已审批
    status = db.Column(db.String(20), default='draft')
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<MonthlyReport {self.year}-{self.month}>' 