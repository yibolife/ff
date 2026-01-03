from flask_wtf import FlaskForm
from wtforms import DateTimeField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import DateTimeInput
from markupsafe import Markup

# 自定义时间选择器控件
class DateTimeLocalInput(DateTimeInput):
    input_type = 'datetime-local'

    def __call__(self, field, **kwargs):
        if field.data:
            kwargs['value'] = field.data.strftime('%Y-%m-%dT%H:%M')
        return Markup(super().__call__(field, **kwargs))

class AgentInfoForm(FlaskForm):
    time = DateTimeField(
        '时间',
        validators=[Optional()],
        format='%Y-%m-%dT%H:%M',
        widget=DateTimeLocalInput()
    )
    location = StringField(
        '地点',
        validators=[DataRequired(message='请填写代购地点'), Length(max=100, message='地点不能超过100字')]
    )
    itinerary = TextAreaField(
        '行程计划',
        validators=[
            DataRequired(message='请填写行程安排'),
            Length(min=10, message='行程安排至少10个字符')
        ]
    )
    save_submit = SubmitField('保存代购信息')

class AgentSubmitForm(FlaskForm):
    join_submit = SubmitField('加入代购圈')

class AgentDeleteForm(FlaskForm):
    delete_submit = SubmitField('删除代购信息')