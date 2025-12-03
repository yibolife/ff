# app/forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from app.models.user import User  # 导入用户模型，用于用户名/手机号唯一性验证

# ------------------------------
# 登录表单（LoginForm）
# ------------------------------
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired('用户名不能为空'),
        Length(3, 20, '用户名长度需在 3-20 位之间')
    ])
    submit = SubmitField('登录')

# ------------------------------
# 注册表单（RegistrationForm，与导入的类名一致）
# ------------------------------
class RegistrationForm(FlaskForm):  # 类名改为 RegistrationForm，匹配导入语句
    username = StringField('用户名', validators=[
        DataRequired('用户名不能为空'),
        Length(3, 20, '用户名长度需在 3-20 位之间')
    ])
    phone = StringField('手机号', validators=[
        DataRequired('手机号不能为空'),
        Regexp(r'^1[3-9]\d{9}$', message='请输入有效的 11 位中国大陆手机号')
    ])
    verify_code = StringField('验证码', validators=[
        DataRequired('验证码不能为空'),
        Length(6, 6, '验证码必须为 6 位')
    ])
    submit = SubmitField('注册')

    # 自定义验证：用户名已存在
    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError('该用户名已被注册，请更换')

    # 自定义验证：手机号已存在
    def validate_phone(self, field):
        if User.query.filter_by(phone=field.data.strip()).first():
            raise ValidationError('该手机号已被注册，请更换')

# ------------------------------
# 身份选择表单（AgentChoiceForm，补充缺失的类）
# ------------------------------
class AgentChoiceForm(FlaskForm):  # 新增：身份选择表单（普通用户/代购用户）
    identity_type = RadioField(
        '请选择用户身份',
        choices=[('normal', '普通用户'), ('agent', '代购用户')],  # 选项值+显示文本
        validators=[DataRequired('请选择身份类型')],
        default='normal'  # 默认选择普通用户
    )
    submit = SubmitField('确认选择')