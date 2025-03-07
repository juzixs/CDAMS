from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class TicketForm(FlaskForm):
    """工单创建表单"""
    title = StringField('标题', validators=[DataRequired(), Length(min=3, max=100)])
    content = TextAreaField('内容', validators=[DataRequired(), Length(min=10, max=2000)])
    priority = SelectField('优先级', choices=[
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急')
    ], validators=[DataRequired()])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    submit = SubmitField('提交工单')

class TicketReplyForm(FlaskForm):
    """工单回复表单"""
    content = TextAreaField('回复内容', validators=[DataRequired(), Length(min=2, max=1000)])
    submit = SubmitField('提交回复')

class TicketCategoryForm(FlaskForm):
    """工单分类表单"""
    name = StringField('分类名称', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('分类描述', validators=[Length(max=200)])
    submit = SubmitField('保存') 