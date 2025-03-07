from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf.file import FileField, FileAllowed

class DormitoryForm(FlaskForm):
    """宿舍表单"""
    name = StringField('宿舍名称', validators=[DataRequired(message='请输入宿舍名称')])
    address = StringField('宿舍地址')
    type = SelectField('宿舍类型', choices=[('自有', '自有'), ('租赁', '租赁')])
    lease_start_date = DateField('起租时间', format='%Y-%m-%d', validators=[Optional()])
    lease_end_date = DateField('到期时间', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('提交')

    def validate_lease_dates(self, field):
        """验证租赁日期"""
        if self.type.data == '租赁':
            if not self.lease_start_date.data:
                raise ValidationError('请输入起租时间')
            if not self.lease_end_date.data:
                raise ValidationError('请输入到期时间')
            if self.lease_start_date.data and self.lease_end_date.data and self.lease_start_date.data > self.lease_end_date.data:
                raise ValidationError('起租时间不能晚于到期时间')


class RoomForm(FlaskForm):
    """房间表单"""
    room_number = StringField('房间号', validators=[DataRequired(message='请输入房间号')])
    floor = IntegerField('楼层', validators=[DataRequired(message='请输入楼层号')])
    capacity = IntegerField('容纳人数', validators=[DataRequired(message='请输入房间容纳人数')])
    room_type = SelectField('房间类型', choices=[
        ('男工宿舍', '男工宿舍'),
        ('女工宿舍', '女工宿舍'),
        ('高管间', '高管间'),
        ('访客间', '访客间')
    ])
    facilities = StringField('房间配置', description='以逗号分隔的标签，如: 空调,电视,独卫')
    submit = SubmitField('提交')


class ResidentForm(FlaskForm):
    """住户表单"""
    name = StringField('姓名', validators=[DataRequired(message='请输入姓名')])
    gender = SelectField('性别', choices=[('男', '男'), ('女', '女')], validators=[DataRequired(message='请选择性别')])
    department = StringField('部门')
    position = StringField('岗位')
    phone = StringField('手机')
    remarks = TextAreaField('备注')
    submit = SubmitField('提交') 