from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea

class VehicleExitForm(FlaskForm):
    """车辆出门表单"""
    # 基本信息
    exit_type = HiddenField('出门类型', validators=[DataRequired()])
    
    # 申请信息
    department = StringField('申请部门', validators=[Optional(), Length(max=100)])
    initiator = StringField('发起人', validators=[Optional(), Length(max=50)])
    certificate_number = StringField('门证编号', validators=[Optional(), Length(max=50)])
    
    # 车辆和司机信息
    plate_number = StringField('车牌号', validators=[DataRequired(), Length(max=20)])
    driver_name = StringField('驾驶员姓名', validators=[DataRequired(), Length(max=50)])
    phone = StringField('司机联系电话', validators=[Optional(), Length(max=20)])
    id_number = StringField('身份证号码', validators=[Optional(), Length(max=30)])
    
    # 物流信息
    vehicle_type = SelectField('车型', choices=[
        ('truck', '货车'),
        ('tractor', '拖拉机'),
        ('express', '快递'),
        ('other', '其他')
    ], validators=[Optional()])
    
    logistics_type = SelectField('物流方式', choices=[
        ('company', '公司自有车辆'),
        ('logistics', '物流公司车辆'),
        ('outsourcing', '外协车辆')
    ], validators=[Optional()])
    
    logistics_company = StringField('物流公司名称', validators=[Optional(), Length(max=100)])
    logistics_number = StringField('物流单号', validators=[Optional(), Length(max=50)])
    
    # 物品和目的地信息
    company = StringField('接收单位', validators=[Optional(), Length(max=100)])
    
    item_category = SelectField('出厂物品分类', choices=[
        ('product', '产成品交付'),
        ('outsourcing', '外协'),
        ('material', '园区物料周转'),
        ('other', '其他')
    ], validators=[Optional()])
    
    destination = StringField('目的地', validators=[Optional(), Length(max=200)])
    items = TextAreaField('携带物品', validators=[Optional()], widget=TextArea())
    purpose = StringField('出门事由', validators=[Optional(), Length(max=200)])
    
    # 时间信息
    exit_time = DateTimeField('申请出厂日期', format='%Y-%m-%d', validators=[Optional()])
    expected_return_time = DateTimeField('预计返回时间', format='%Y-%m-%d', validators=[Optional()])
    confirmed_exit_time = DateTimeField('确认出厂日期', format='%Y-%m-%d', validators=[Optional()])
    
    # 审批信息
    reviewer = StringField('审核人', validators=[Optional(), Length(max=50)])
    issuer = StringField('发放人', validators=[Optional(), Length(max=50)])
    approver_name = StringField('审批人', validators=[Optional(), Length(max=50)])
    guard = StringField('门卫', validators=[Optional(), Length(max=50)])
    
    # 备注
    remarks = TextAreaField('备注', validators=[Optional()], widget=TextArea()) 