# app/forms/binding_forms.py
from flask_wtf import FlaskForm
from wtforms import SubmitField  # 提交按钮（可选，也可在模板手动写按钮）

class ConfirmBindingForm(FlaskForm):
    """确认绑定表单（仅用于 CSRF 保护和提交验证）"""
    submit = SubmitField('确认绑定')  # 提交按钮（模板中可直接使用 form.submit）

# 解除绑定表单（新增，空表单仅用于 CSRF）
class UnbindForm(FlaskForm):
    pass  # 无需额外字段，Flask-WTF 自动生成 CSRF 令牌