from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app  # 导入 current_app
from flask_login import login_required, current_user
from app import db  # 仅导入扩展，不导入 app
from app.forms import ShoppingInfoForm, ShoppingSubmitForm, DeleteShoppingItemForm
from app.models import ShoppingInfo, ShoppingCircle, User, AgentInfo, Binding
import os
from datetime import datetime

shopping_bp = Blueprint('shopping', __name__)

@shopping_bp.route('/shopping-info', methods=['GET', 'POST'])
@login_required
def shopping_info():
    if current_user.is_agent:
        return redirect(url_for('auth.choice'))

    shopping_items = current_user.shopping_info
    total_price = sum(item.price for item in shopping_items) if shopping_items else 0.0

    form = ShoppingInfoForm()
    submit_form = ShoppingSubmitForm()
    delete_form = DeleteShoppingItemForm()

    # 正确：用 current_app.config 获取上传目录，不直接引用 app
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 添加商品
    if 'add_product' in request.form and form.validate_on_submit():
        image_filename = None
        if form.product_image.data:
            image = form.product_image.data
            image_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename.replace(' ', '_')[:50]}"
            if len(image_filename) > 100:
                image_filename = image_filename[:97] + '...'
            image.save(os.path.join(upload_folder, image_filename))

        new_item = ShoppingInfo(
            serial_number=form.serial_number.data,
            product_name=form.product_name.data,
            price=float(form.price.data),
            product_image=image_filename,
            description=form.description.data,
            user=current_user
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f'商品【{form.product_name.data}】添加成功', 'success')
        return redirect(url_for('shopping.shopping_info'), code=303)

    # 提交购物圈
    if 'submit_shopping' in request.form and submit_form.validate_on_submit():
        if not shopping_items:
            flash('请先添加商品再提交', 'warning')
            return redirect(url_for('shopping.shopping_info'), code=303)

        existing_circle = current_user.shopping_circle
        if existing_circle:
            existing_circle.total_price = total_price
            existing_circle.submit_time = datetime.utcnow()
        else:
            new_circle = ShoppingCircle(
                user=current_user,
                total_price=total_price
            )
            db.session.add(new_circle)

        db.session.commit()
        return redirect(url_for('agent.agent_circle'), code=303)

    # 删除商品
    if 'delete_item' in request.form:
        item_id = request.form.get('item_id')
        if not item_id or not item_id.isdigit():
            flash('删除失败：商品ID无效', 'danger')
            return redirect(url_for('shopping.shopping_info'), code=303)

        item_id = int(item_id)
        item = ShoppingInfo.query.filter_by(id=item_id, user=current_user).first()
        if not item:
            flash('删除失败：商品不存在或无权删除', 'danger')
            return redirect(url_for('shopping.shopping_info'), code=303)

        # 删除图片
        if item.product_image:
            image_path = os.path.join(upload_folder, item.product_image)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    flash(f'商品删除成功，但图片清理失败：{str(e)}', 'warning')

        db.session.delete(item)
        db.session.commit()
        flash(f'商品【{item.product_name}】已删除', 'success')
        return redirect(url_for('shopping.shopping_info'), code=303)

    return render_template(
        'shopping_info.html',
        form=form,
        submit_form=submit_form,
        delete_form=delete_form,
        shopping_items=shopping_items,
        total_price=total_price
    )

# 代购查看购物圈页面
@shopping_bp.route('/shopping-circle')
@login_required
def shopping_circle():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    elif not current_user.is_agent:
        flash('仅代购用户可访问购物圈', 'warning')
        return redirect(url_for('auth.choice'))

    # 查询非代购用户的购物圈
    non_agent_users = User.query.filter_by(is_agent=False).all()
    shopping_data = [
        {
            "user": user,
            "circle_info": shopping_circle,
            "products": ShoppingInfo.query.filter_by(user_id=user.id).all(),
        }
        for user in non_agent_users
        if (shopping_circle := ShoppingCircle.query.filter_by(user_id=user.id).first())
           and not Binding.query.filter_by(buyer_id=user.id).first()
    ]

    # 检查代购是否有有效行程
    has_valid_itinerary = False
    agent_itinerary = current_user.agent_itinerary
    if agent_itinerary:
        if agent_itinerary.is_submitted and agent_itinerary.time >= datetime.now():
            has_valid_itinerary = True

    return render_template(
        'shopping_circle.html',
        shopping_data=shopping_data,
        has_valid_itinerary=has_valid_itinerary
    )

# 已代购商品页面（普通用户/代购用户都可访问）
@shopping_bp.route('/purchased_products')
@login_required
def purchased_products():
    from app.models import Binding
    if current_user.is_agent:
        bindings = Binding.query.filter_by(agent_id=current_user.id).all()
    else:
        bindings = Binding.query.filter_by(buyer_id=current_user.id).all()

    enriched_trips = []
    for binding in bindings:
        # 代购信息
        agent_id = binding.agent_id if not current_user.is_agent else current_user.id
        agent_itinerary = AgentInfo.query.filter_by(user_id=agent_id).first()
        agent_user = User.query.filter_by(id=agent_id).first()

        # 买家信息
        buyer_id = binding.buyer_id if current_user.is_agent else current_user.id
        buyer = User.query.filter_by(id=buyer_id).first()

        # 购物信息
        buyer_circle = ShoppingCircle.query.filter_by(user_id=buyer_id).first()
        buyer_products = ShoppingInfo.query.filter_by(user_id=buyer_id).all() if buyer_circle else []

        enriched_trips.append({
            "binding": binding,
            "agent_itinerary": agent_itinerary,
            "agent_user": agent_user,
            "buyer": buyer,
            "buyer_circle": buyer_circle,
            "buyer_products": buyer_products
        })

    return render_template('purchased_products.html', trips=enriched_trips)

# 聊天页面
@shopping_bp.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    return render_template('chat.html', other_user=other_user)