from datetime import datetime
from app import db
from app.models import User

class TicketCategory(db.Model):
    """工单分类模型"""
    __tablename__ = 'ticket_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<TicketCategory {self.name}>'

class Ticket(db.Model):
    """工单模型"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, closed, resolved
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('ticket_categories.id'))
    
    # 关系
    replies = db.relationship('TicketReply', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('tickets', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'
    
    @property
    def status_display(self):
        """返回状态的显示名称"""
        status_map = {
            'pending': '待处理',
            'processing': '处理中',
            'closed': '已关闭',
            'resolved': '已解决'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def priority_display(self):
        """返回优先级的显示名称"""
        priority_map = {
            'low': '低',
            'medium': '中',
            'high': '高',
            'urgent': '紧急'
        }
        return priority_map.get(self.priority, self.priority)
    
    @property
    def priority_class(self):
        """返回优先级对应的CSS类名"""
        priority_class_map = {
            'low': 'text-success',
            'medium': 'text-primary',
            'high': 'text-warning',
            'urgent': 'text-danger'
        }
        return priority_class_map.get(self.priority, '')
    
    @property
    def status_class(self):
        """返回状态对应的CSS类名"""
        status_class_map = {
            'pending': 'bg-warning',
            'processing': 'bg-info',
            'closed': 'bg-secondary',
            'resolved': 'bg-success'
        }
        return status_class_map.get(self.status, '')

class TicketReply(db.Model):
    """工单回复模型"""
    __tablename__ = 'ticket_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关系
    user = db.relationship('User', backref=db.backref('ticket_replies', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TicketReply {self.id}>' 