from flask import Blueprint, render_template, redirect, url_for, flash, request, get_flashed_messages
from flask_login import login_required, current_user
from app import db
from app.forms import AgentInfoForm, AgentSubmitForm, AgentDeleteForm
from app.models import AgentInfo, User, ShoppingCircle, ShoppingInfo, Binding
from app.forms.binding_forms import UnbindForm

agent_bp = Blueprint('agent', __name__)

# 代购行程信息路由
@agent_bp.route('/agent-info', methods=['GET', 'POST'])
@login_required
def agent_info():
    if not current_user.is_agent:
        flash('仅代购用户可访问此页面', 'warning')
        return redirect(url_for('auth.choice'))

    existing_info = AgentInfo.query.filter_by(user_id=current_user.id).first()
    form = AgentInfoForm(obj=existing_info)
    submit_form = AgentSubmitForm()
    delete_form = AgentDeleteForm()

    redirect_source = request.args.get('redirect_source')
    target_buyer_id = request.args.get('target_buyer_id')

    # 保存代购信息
    if form.validate_on_submit() and form.save_submit.data:
        if not form.time.data:
            flash('代购时间为必填项，请选择时间', 'danger')
            return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

        if existing_info:
            existing_info.time = form.time.data
            existing_info.location = form.location.data
            existing_info.itinerary = form.itinerary.data
        else:
            new_info = AgentInfo(
                time=form.time.data,
                location=form.location.data,
                itinerary=form.itinerary.data,
                user_id=current_user.id,
                is_submitted=False
            )
            db.session.add(new_info)

        try:
            db.session.commit()
            flash('代购行程信息已成功保存', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'danger')

        return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

    # 加入代购圈
    if submit_form.validate_on_submit() and submit_form.join_submit.data:
        if not existing_info:
            flash('请先填写并保存代购行程信息', 'warning')
            return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

        existing_info.is_submitted = True
        try:
            db.session.commit()
            flash('已成功加入代购圈！', 'success')
            if redirect_source == 'shopping_circle':
                return redirect(url_for('shopping.shopping_circle'))
            else:
                return redirect(url_for('shopping.shopping_circle'))
        except Exception as e:
            db.session.rollback()
            flash(f'加入代购圈失败：{str(e)}', 'danger')
            return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

    # 删除行程
    if delete_form.validate_on_submit() and delete_form.delete_submit.data:
        if not existing_info:
            flash('没有可删除的代购行程信息', 'warning')
            return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

        try:
            related_bindings = Binding.query.filter_by(agent_id=current_user.id).all()
            for binding in related_bindings:
                db.session.delete(binding)
            db.session.delete(existing_info)
            db.session.commit()
            flash(f'代购行程已删除，解除了 {len(related_bindings)} 个绑定关系', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'删除失败：{str(e)}', 'danger')
        return redirect(url_for('agent.agent_info', redirect_source=redirect_source, target_buyer_id=target_buyer_id))

    return render_template(
        'agent_info.html',
        form=form,
        submit_form=submit_form,
        delete_form=delete_form,
        existing_info=existing_info,
        redirect_source=redirect_source,
        target_buyer_id=target_buyer_id
    )

# 代购圈列表（非代购用户查看代购）
@agent_bp.route('/agent-circle')
@login_required
def agent_circle():
    agent_users = User.query.filter_by(is_agent=True).all()
    agent_data = []
    for user in agent_users:
        agent_info = AgentInfo.query.filter_by(user_id=user.id).first()
        if agent_info and agent_info.is_submitted and agent_info.itinerary.strip():
            agent_data.append({
                "user": user,
                "agent_info": agent_info
            })
    messages = get_flashed_messages(with_categories=True)
    return render_template('agent_circle.html', agent_data=agent_data, messages=messages)

# 代购列表（非代购用户绑定代购）
@agent_bp.route('/agent_list')
def agent_list():
    agent_data = db.session.query(User, AgentInfo).join(
        AgentInfo,
        User.id == AgentInfo.user_id
    ).filter(AgentInfo.is_submitted == True).all()

    agent_data = [
        {
            'user': user,
            'agent_info': info,
            'agent_name': user.username
        } for user, info in agent_data
    ]
    return render_template('agent_list.html', agent_data=agent_data)

# 代购已联系行程页面
@agent_bp.route('/contacted_trips')
@login_required
def contacted_trips():
    if not current_user.is_agent:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('home'))

    bindings = Binding.query.filter_by(agent_id=current_user.id) \
        .join(User, Binding.buyer_id == User.id) \
        .add_columns(User) \
        .order_by(Binding.created_at.desc()) \
        .all()

    agent_itinerary = AgentInfo.query.filter_by(user_id=current_user.id).first()
    enriched_trips = []
    for binding, buyer in bindings:
        buyer_circle = ShoppingCircle.query.filter_by(user_id=buyer.id).first()
        buyer_products = ShoppingInfo.query.filter_by(user_id=buyer.id).all() if buyer_circle else []
        enriched_trips.append({
            "binding": binding,
            "buyer": buyer,
            "buyer_circle": buyer_circle,
            "buyer_products": buyer_products,
            "agent_itinerary": agent_itinerary
        })

    if not enriched_trips:
        flash('暂无已绑定的买家行程，可前往购物圈绑定新买家', 'info')

    unbind_form = UnbindForm()
    return render_template('contacted_trips.html', trips=enriched_trips, form=unbind_form)