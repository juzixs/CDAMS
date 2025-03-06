from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

class VehicleForm(FlaskForm):
    plate_number = StringField('车牌号', validators=[DataRequired(), Length(max=20)])
    vehicle_type = SelectField('车辆类型', 
                             choices=[('燃油', '燃油'), ('新能源', '新能源')],
                             validators=[DataRequired()])
    owner_name = StringField('车主姓名', validators=[DataRequired(), Length(max=64)])
    department = StringField('所属部门', validators=[DataRequired(), Length(max=64)])
    remarks = TextAreaField('备注')
    submit = SubmitField('提交') 