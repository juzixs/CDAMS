from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, IntegerField, BooleanField, SelectField, PasswordField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, Length, EqualTo

class PDFSettingsForm(FlaskForm):
    """PDF设置表单"""
    background_image = FileField('背景图', validators=[
        FileAllowed(['jpg', 'png'], '只允许上传jpg或png格式的图片')
    ])
    font_family = FileField('字体文件', validators=[
        FileAllowed(['ttf', 'otf'], '只允许上传ttf或otf格式的字体文件')
    ])
    font_size = IntegerField('字体大小', validators=[DataRequired()])
    font_bold = BooleanField('粗体')
    text_x = IntegerField('文字X坐标', validators=[DataRequired()])
    text_y = IntegerField('文字Y坐标', validators=[DataRequired()])
    text_color = StringField('文字颜色(RGB)', validators=[DataRequired()], 
                           description='示例：255,0,0 代表红色')
    outline_color = StringField('描边颜色(RGB)', validators=[DataRequired()],
                              description='示例：255,0,0 代表红色')
    outline_width = IntegerField('描边宽度', validators=[DataRequired()])

class ProfileForm(FlaskForm):
    """个人资料表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    employee_id = StringField('工号', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('姓名', validators=[DataRequired(), Length(min=2, max=20)])
    department = StringField('部门', validators=[DataRequired(), Length(max=50)])
    phone = StringField('手机', validators=[DataRequired(), Length(min=11, max=11)])
    password = PasswordField('密码', validators=[Optional(), Length(min=6, message='密码长度不能小于6个字符')])
    confirm_password = PasswordField('确认密码', validators=[
        Optional(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('保存')

class PasswordForm(FlaskForm):
    """密码修改表单"""
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[
        DataRequired(),
        Length(min=6, message='密码长度不能小于6个字符')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('修改密码')

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class UserCreateForm(FlaskForm):
    """用户创建表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, message='密码长度不能小于6个字符')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    employee_id = StringField('工号', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('姓名', validators=[DataRequired(), Length(min=2, max=20)])
    department = StringField('部门', validators=[DataRequired(), Length(max=50)])
    phone = StringField('手机', validators=[DataRequired(), Length(min=11, max=11)])
    is_admin = BooleanField('管理员权限')
    submit = SubmitField('创建用户')

class UserSearchForm(FlaskForm):
    """用户搜索表单"""
    keyword = StringField('关键词', validators=[Optional()])
    field = SelectField('搜索字段', choices=[
        ('username', '用户名'),
        ('employee_id', '工号'),
        ('name', '姓名'),
        ('department', '部门'),
        ('phone', '手机'),
        ('email', '邮箱')
    ])
    submit = SubmitField('搜索') 