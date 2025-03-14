from datetime import datetime
from app import db
from sqlalchemy import Enum
import enum

class CarStatus(enum.Enum):
    idle = '空闲'
    dispatched = '派出'
    borrowed = '借出'
    maintenance = '维保'
    scrapped = '报废'

class OfficialCar(db.Model):
    """公务车辆信息模型"""
    __tablename__ = 'official_cars'

    id = db.Column(db.Integer, primary_key=True)
    sequence_number = db.Column(db.Integer, comment='序号')
    card_number = db.Column(db.String(50), comment='卡片编号')
    asset_number = db.Column(db.String(50), nullable=False, comment='资产编号')
    brand = db.Column(db.String(50), comment='品牌')
    asset_description = db.Column(db.String(200), comment='资产描述')
    model = db.Column(db.String(100), comment='规格型号')
    original_value = db.Column(db.Float, comment='原值')
    is_business_car = db.Column(db.String(100), comment='经营用车')
    business_status = db.Column(db.String(100), comment='使用状况')
    plate_number = db.Column(db.String(20), comment='车牌号')
    car_model = db.Column(db.String(100), comment='车辆型号')
    car_type = db.Column(db.String(100), comment='车型')
    registration_time = db.Column(db.DateTime, comment='登记时间')
    seat_count = db.Column(db.Integer, comment='座位数')
    displacement = db.Column(db.String(50), comment='排气量')
    responsible_person = db.Column(db.String(50), comment='责任人')
    usage_nature = db.Column(db.String(50), comment='使用性质')
    vehicle_license = db.Column(db.String(255), comment='车辆行驶证文件路径')
    
    # 状态信息
    status = db.Column(db.Enum(CarStatus), default=CarStatus.idle, comment='车辆状态')
    is_scrapped = db.Column(db.Boolean, default=False, comment='是否报废')
    scrap_time = db.Column(db.DateTime, comment='报废时间')
    scrapped_by = db.Column(db.Integer, comment='报废操作人ID')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, comment='创建人ID')
    updated_by = db.Column(db.Integer, comment='更新人ID')
    
    # 关联记录
    usage_records = db.relationship('CarUsageRecord', backref='car', lazy='dynamic', cascade='all, delete-orphan')
    maintenance_records = db.relationship('CarMaintenanceRecord', backref='car', lazy='dynamic', cascade='all, delete-orphan')
    fuel_records = db.relationship('CarFuelRecord', backref='car', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OfficialCar {self.plate_number} {self.asset_number}>'

class CarUsageRecord(db.Model):
    """车辆使用记录模型"""
    __tablename__ = 'car_usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    
    # 申请信息
    applicant = db.Column(db.String(50), nullable=False, comment='申请人')
    department = db.Column(db.String(50), comment='部门')
    phone = db.Column(db.String(20), comment='联系电话')
    
    # 用车信息
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    expected_end_time = db.Column(db.DateTime, nullable=False, comment='预计结束时间')
    actual_end_time = db.Column(db.DateTime, comment='实际结束时间')
    passengers = db.Column(db.Integer, comment='乘车人数')
    destination = db.Column(db.String(100), comment='目的地')
    purpose = db.Column(db.String(200), comment='用车事由')
    
    # 里程信息
    start_mileage = db.Column(db.Float, comment='起始里程')
    end_mileage = db.Column(db.Float, comment='结束里程')
    
    # 审批信息
    status = db.Column(db.String(20), default='pending', comment='状态：pending（待审核）, approved（已批准）, rejected（已拒绝）, completed（已完成）')
    approver = db.Column(db.String(50), comment='审批人')
    
    # 备注
    remarks = db.Column(db.Text, comment='备注')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<CarUsageRecord {self.id} {self.car_id}>'

class CarMaintenanceRecord(db.Model):
    """车辆维修保养记录模型"""
    __tablename__ = 'car_maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    
    # 维修保养信息
    maintenance_type = db.Column(db.String(20), comment='类型：maintenance（保养）, repair（维修）')
    maintenance_time = db.Column(db.DateTime, nullable=False, comment='维修保养时间')
    maintenance_location = db.Column(db.String(100), comment='维修保养地点')
    maintenance_items = db.Column(db.Text, comment='维修保养项目')
    current_mileage = db.Column(db.Float, comment='当前里程')
    
    # 费用信息
    cost = db.Column(db.Float, comment='费用')
    invoice_number = db.Column(db.String(50), comment='发票号码')
    invoice_file = db.Column(db.String(255), comment='发票文件路径')
    
    # 负责人信息
    responsible_person = db.Column(db.String(50), comment='负责人')
    
    # 备注
    remarks = db.Column(db.Text, comment='备注')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<CarMaintenanceRecord {self.id} {self.car_id}>'

class CarFuelRecord(db.Model):
    """车辆加油充值记录模型"""
    __tablename__ = 'car_fuel_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    
    # 加油充值信息
    fuel_type = db.Column(db.String(20), comment='类型：gas（加油）, charge（充电）')
    fuel_time = db.Column(db.DateTime, nullable=False, comment='加油充值时间')
    fuel_location = db.Column(db.String(100), comment='加油充值地点')
    fuel_amount = db.Column(db.Float, comment='加油量/充电量')
    current_mileage = db.Column(db.Float, comment='当前里程')
    
    # 费用信息
    cost = db.Column(db.Float, comment='费用')
    invoice_number = db.Column(db.String(50), comment='发票号码')
    invoice_file = db.Column(db.String(255), comment='发票文件路径')
    
    # 负责人信息
    responsible_person = db.Column(db.String(50), comment='负责人')
    
    # 备注
    remarks = db.Column(db.Text, comment='备注')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<CarFuelRecord {self.id} {self.car_id}>' 