from flask_wtf import FlaskForm
from wtforms import StringField, FileField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class ShoppingInfoForm(FlaskForm):
    serial_number = StringField('序号', validators=[DataRequired(), Length(max=20)])
    product_name = StringField('商品名称', validators=[DataRequired(), Length(max=100)])
    price = StringField('价格（元）', validators=[
        DataRequired(),
        Regexp(r'^\d+(\.\d{1,2})?$', message='请输入有效的价格（最多两位小数）')
    ])
    product_image = FileField('商品图片')
    description = TextAreaField('商品描述')
    submit = SubmitField('添加商品', name='add_product')

class ShoppingSubmitForm(FlaskForm):
    submit = SubmitField('加入购物圈', name='submit_shopping')

class DeleteShoppingItemForm(FlaskForm):
    submit = SubmitField('删除', name='delete_item')