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
    insurance_records = db.relationship('CarInsurance', backref='car', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OfficialCar {self.plate_number} {self.asset_number}>'

class CarUsageRecord(db.Model):
    """车辆使用记录模型"""
    __tablename__ = 'car_usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    
    # 申请信息
    department = db.Column(db.String(50), nullable=False, comment='申请使用部门')
    plate_number = db.Column(db.String(20), nullable=False, comment='使用车牌号')
    
    # 出车信息
    departure_date = db.Column(db.Date, nullable=False, comment='出车日期')
    departure_time = db.Column(db.Time, nullable=False, comment='出车时间')
    departure_mileage = db.Column(db.Float, comment='出车里程')
    destination_purpose = db.Column(db.String(200), comment='出车去向及事由')
    
    # 收车信息
    return_time = db.Column(db.DateTime, comment='收车时间')
    return_mileage = db.Column(db.Float, comment='收车里程')
    
    # 使用信息
    usage_duration = db.Column(db.String(20), comment='使用时长')
    driver = db.Column(db.String(50), comment='驾驶员')
    passengers = db.Column(db.String(200), comment='随同人员')
    
    # 费用信息
    refueling = db.Column(db.Boolean, default=False, comment='加油')
    maintenance = db.Column(db.String(200), comment='维修')
    toll_fee = db.Column(db.String(50), comment='过路过桥费')
    parking_fee = db.Column(db.String(50), comment='停车费')
    accident_violation = db.Column(db.String(200), comment='交通事故、违章')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, comment='创建人ID')
    updated_by = db.Column(db.Integer, comment='更新人ID')
    
    def __repr__(self):
        return f'<CarUsageRecord {self.id} {self.plate_number}>'

class CarMaintenanceRecord(db.Model):
    """车辆维修保养记录模型"""
    __tablename__ = 'car_maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    
    # 维修保养信息
    application_time = db.Column(db.Date, nullable=False, comment='申请时间')
    car_type = db.Column(db.String(100), comment='车型')
    plate_number = db.Column(db.String(20), nullable=False, comment='车牌号')
    driver = db.Column(db.String(50), comment='驾驶员')
    sender = db.Column(db.String(50), comment='送修人')
    reason = db.Column(db.Text, comment='送修原因')
    maintenance_location = db.Column(db.String(100), comment='维修厂')
    cost = db.Column(db.Float, comment='维修费用')
    completion_time = db.Column(db.Date, comment='完成时间')
    remarks = db.Column(db.Text, comment='备注')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, comment='创建人ID')
    updated_by = db.Column(db.Integer, comment='更新人ID')
    
    def __repr__(self):
        return f'<CarMaintenanceRecord {self.id} {self.plate_number}>'

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

class CarInsurance(db.Model):
    """车辆保险记录模型"""
    __tablename__ = 'car_insurance'

    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('official_cars.id'), nullable=False, comment='车辆ID')
    plate_number = db.Column(db.String(20), nullable=False, comment='车牌号')
    car_type = db.Column(db.String(100), comment='车型')
    amount = db.Column(db.Float, nullable=False, comment='保险金额')
    insurance_start_date = db.Column(db.Date, nullable=False, comment='保险开始日期')
    insurance_end_date = db.Column(db.Date, nullable=False, comment='保险结束日期')
    renewal_date = db.Column(db.Date, nullable=False, comment='续保日期')
    
    # 系统信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, comment='创建人ID')
    updated_by = db.Column(db.Integer, comment='更新人ID') 