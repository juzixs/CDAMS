from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, BooleanField, DateTimeField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class OfficialCarForm(FlaskForm):
    """公务车辆信息表单"""
    card_number = StringField('卡片编号')
    asset_number = StringField('资产编号', validators=[DataRequired(message='资产编号必填')])
    brand = StringField('品牌')
    asset_description = StringField('资产描述')
    model = StringField('规格型号')
    original_value = FloatField('原值', validators=[Optional()])
    is_business_car = StringField('经营用车')
    plate_number = StringField('车牌号')
    car_model = StringField('车辆型号')
    car_type = StringField('车型')
    registration_time = DateTimeField('登记时间', format='%Y-%m-%d', validators=[Optional()])
    seat_count = IntegerField('座位数', validators=[Optional(), NumberRange(min=1, message='座位数必须大于0')])
    displacement = StringField('排气量')
    responsible_person = StringField('责任人')
    usage_nature = StringField('使用性质')
    vehicle_license = FileField('车辆行驶证', validators=[Optional(), FileAllowed(['jpg', 'png', 'pdf'], '只允许上传JPG, PNG和PDF文件')])
    submit = SubmitField('提交')

class CarUsageRecordForm(FlaskForm):
    """车辆使用记录表单"""
    department = StringField('申请使用部门', validators=[DataRequired(message='申请使用部门必填')])
    plate_number = StringField('使用车牌号', validators=[DataRequired(message='使用车牌号必填')])
    departure_date = DateTimeField('出车日期', format='%Y-%m-%d', validators=[DataRequired(message='出车日期必填')])
    departure_time = StringField('出车时间', validators=[DataRequired(message='出车时间必填')])
    departure_mileage = FloatField('出车里程', validators=[Optional()])
    destination_purpose = TextAreaField('出车去向及事由', validators=[Optional()])
    driver = StringField('驾驶员', validators=[Optional()])
    passengers = TextAreaField('随同人员', validators=[Optional()])
    submit = SubmitField('提交')

class CarReturnForm(FlaskForm):
    """车辆收车表单"""
    return_time = DateTimeField('收车时间', format='%Y-%m-%d %H:%M', validators=[DataRequired(message='收车时间必填')])
    return_mileage = FloatField('收车里程', validators=[Optional()])
    refueling = BooleanField('加油', default=False)
    maintenance = StringField('维修', validators=[Optional()])
    toll_fee = StringField('过路过桥费', validators=[Optional()])
    parking_fee = StringField('停车费', validators=[Optional()])
    accident_violation = TextAreaField('交通事故、违章', validators=[Optional()])
    submit = SubmitField('提交')

class CarUsageRecordFullForm(FlaskForm):
    """完整的车辆使用记录表单（用于添加记录）"""
    department = StringField('申请使用部门', validators=[DataRequired(message='申请使用部门必填')])
    plate_number = SelectField('使用车牌号', validators=[DataRequired(message='使用车牌号必填')])
    departure_date = DateTimeField('出车日期', format='%Y-%m-%d', validators=[DataRequired(message='出车日期必填')])
    departure_time = StringField('出车时间', validators=[DataRequired(message='出车时间必填')])
    departure_mileage = FloatField('出车里程', validators=[Optional()])
    destination_purpose = TextAreaField('出车去向及事由', validators=[Optional()])
    return_time = DateTimeField('收车时间', format='%Y-%m-%d %H:%M', validators=[Optional()])
    return_mileage = FloatField('收车里程', validators=[Optional()])
    driver = StringField('驾驶员', validators=[Optional()])
    passengers = TextAreaField('随同人员', validators=[Optional()])
    refueling = BooleanField('加油', default=False)
    maintenance = StringField('维修', validators=[Optional()])
    toll_fee = StringField('过路过桥费', validators=[Optional()])
    parking_fee = StringField('停车费', validators=[Optional()])
    accident_violation = TextAreaField('交通事故、违章', validators=[Optional()])
    submit = SubmitField('提交')

class CarMaintenanceRecordForm(FlaskForm):
    """车辆维修保养记录表单"""
    car_id = SelectField('车辆', coerce=int, validators=[DataRequired(message='请选择车辆')])
    maintenance_type = SelectField('维修保养类型', choices=[('maintenance', '保养'), ('repair', '维修')])
    maintenance_time = DateTimeField('维修保养时间', format='%Y-%m-%d %H:%M', validators=[DataRequired(message='请选择维修保养时间')])
    maintenance_location = StringField('维修保养地点')
    maintenance_items = TextAreaField('维修保养项目')
    current_mileage = FloatField('当前里程', validators=[Optional()])
    cost = FloatField('费用', validators=[Optional()])
    invoice_number = StringField('发票号码')
    invoice_file = FileField('发票', validators=[Optional(), FileAllowed(['jpg', 'png', 'pdf'], '只允许上传JPG, PNG和PDF文件')])
    responsible_person = StringField('负责人')
    remarks = TextAreaField('备注')
    submit = SubmitField('提交')

class CarFuelRecordForm(FlaskForm):
    """车辆加油充值记录表单"""
    car_id = SelectField('车辆', coerce=int, validators=[DataRequired(message='请选择车辆')])
    fuel_type = SelectField('加油充值类型', choices=[('gas', '加油'), ('charge', '充电')])
    fuel_time = DateTimeField('加油充值时间', format='%Y-%m-%d %H:%M', validators=[DataRequired(message='请选择加油充值时间')])
    fuel_location = StringField('加油充值地点')
    fuel_amount = FloatField('加油量/充电量', validators=[Optional()])
    current_mileage = FloatField('当前里程', validators=[Optional()])
    cost = FloatField('费用', validators=[Optional()])
    invoice_number = StringField('发票号码')
    invoice_file = FileField('发票', validators=[Optional(), FileAllowed(['jpg', 'png', 'pdf'], '只允许上传JPG, PNG和PDF文件')])
    responsible_person = StringField('负责人')
    remarks = TextAreaField('备注')
    submit = SubmitField('提交') 