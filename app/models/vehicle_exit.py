from datetime import datetime
from app import db

class VehicleExit(db.Model):
    """车辆出门记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    exit_type = db.Column(db.String(20), nullable=False, comment='出门类型：outsourcing（外协）或 product（产成品）')
    
    # 申请信息
    department = db.Column(db.String(100), comment='申请部门')
    initiator = db.Column(db.String(50), comment='发起人')
    certificate_number = db.Column(db.String(50), comment='出门证编号')
    
    # 车辆和司机信息
    plate_number = db.Column(db.String(20), nullable=False, comment='车牌号')
    driver_name = db.Column(db.String(50), nullable=False, comment='驾驶员姓名')
    phone = db.Column(db.String(20), comment='司机联系电话')
    id_number = db.Column(db.String(30), comment='身份证号码')
    
    # 物流信息
    vehicle_type = db.Column(db.String(20), comment='车型：truck（货车）, tractor（拖拉机）, express（快递）, other（其他）')
    logistics_type = db.Column(db.String(20), comment='物流方式：company（公司自有车辆）, logistics（物流公司车辆）, outsourcing（外协车辆）')
    logistics_company = db.Column(db.String(100), comment='物流公司名称')
    logistics_number = db.Column(db.String(50), comment='物流单号')
    
    # 物品和目的地信息
    company = db.Column(db.String(100), comment='接收单位')
    item_category = db.Column(db.String(20), comment='出厂物品分类：product（产成品交付）, outsourcing（外协）, material（园区物料周转）, other（其他）')
    destination = db.Column(db.String(200), comment='目的地')
    items = db.Column(db.Text, comment='携带物品')
    purpose = db.Column(db.String(200), comment='出门事由')
    
    # 时间信息
    exit_time = db.Column(db.DateTime, comment='申请出厂日期')
    expected_return_time = db.Column(db.DateTime, comment='预计返回时间')
    actual_return_time = db.Column(db.DateTime, comment='实际返回时间')
    confirmed_exit_time = db.Column(db.DateTime, comment='确认出厂日期（门卫签字日期）')
    
    # 审批信息
    reviewer = db.Column(db.String(50), comment='审核人')
    issuer = db.Column(db.String(50), comment='发放人')
    approver_text = db.Column(db.String(50), comment='审批人')
    guard = db.Column(db.String(50), comment='门卫')
    
    # 状态和备注
    status = db.Column(db.String(20), default='pending', comment='状态：pending（待审核）, approved（已审核）, completed（已完成）')
    remarks = db.Column(db.Text, comment='备注')
    
    # 系统信息
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='审核人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_exits')
    approver_user = db.relationship('User', foreign_keys=[approved_by], backref='approved_exits')
    
    def __repr__(self):
        return f'<VehicleExit {self.id} {self.plate_number}>' 