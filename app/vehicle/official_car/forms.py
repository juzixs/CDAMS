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
    car_id = SelectField('车辆', coerce=int, validators=[DataRequired(message='请选择车辆')])
    applicant = StringField('申请人', validators=[DataRequired(message='请输入申请人')])
    department = StringField('部门')
    phone = StringField('联系电话')
    start_time = DateTimeField('开始时间', format='%Y-%m-%d %H:%M', validators=[DataRequired(message='请选择开始时间')])
    expected_end_time = DateTimeField('预计结束时间', format='%Y-%m-%d %H:%M', validators=[DataRequired(message='请选择预计结束时间')])
    actual_end_time = DateTimeField('实际结束时间', format='%Y-%m-%d %H:%M', validators=[Optional()])
    passengers = IntegerField('乘车人数', validators=[Optional(), NumberRange(min=1, message='乘车人数必须大于0')])
    destination = StringField('目的地')
    purpose = TextAreaField('用车事由')
    start_mileage = FloatField('起始里程', validators=[Optional()])
    end_mileage = FloatField('结束里程', validators=[Optional()])
    remarks = TextAreaField('备注')
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