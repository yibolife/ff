from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Binding, User

binding_bp = Blueprint('binding', __name__)

# 代购绑定买家
@binding_bp.route('/bind/buyer/<int:buyer_id>')
@login_required
def bind_buyer(buyer_id):
    if not current_user.is_agent:
        flash('只有代购用户可以发起绑定', 'danger')
        return redirect(url_for('shopping.shopping_info'))

    # 检查是否已绑定
    existing_binding = Binding.query.filter_by(
        agent_id=current_user.id,
        buyer_id=buyer_id
    ).first()

    if existing_binding:
        flash('已与用户绑定', 'info')
        return redirect(url_for('binding.binding_detail', buyer_id=buyer_id))

    # 创建绑定
    new_binding = Binding(
        agent_id=current_user.id,
        buyer_id=buyer_id,
        status='pending'
    )
    db.session.add(new_binding)
    db.session.commit()

    flash('绑定请求已发送', 'success')
    return redirect(url_for('binding.binding_detail', buyer_id=buyer_id))

# 普通用户绑定代购
@binding_bp.route('/bind_agent/<int:agent_id>')
@login_required
def bind_agent(agent_id):
    # 验证当前用户不是代购
    if current_user.is_agent:
        flash('代购用户不能绑定其他代购', 'danger')
        return redirect(url_for('agent.agent_list'))

    # 验证目标是代购
    agent_user = User.query.get(agent_id)
    if not agent_user or not agent_user.is_agent:
        flash('无效的代购用户', 'danger')
        return redirect(url_for('agent.agent_list'))

    # 检查是否已绑定
    existing_binding = Binding.query.filter_by(
        buyer_id=current_user.id,
        agent_id=agent_id
    ).first()
    if existing_binding:
        flash('您已与该代购绑定', 'warning')
        return redirect(url_for('agent.agent_list'))

    # 创建绑定
    new_binding = Binding(
        buyer_id=current_user.id,
        agent_id=agent_id,
        status='pending'
    )
    db.session.add(new_binding)
    try:
        db.session.commit()
        flash(f'成功与代购 {agent_user.username} 绑定', 'success')
    except Exception as e:
        db.session.rollback()
        flash('绑定失败，请重试', 'danger')
        print(f'绑定失败：{str(e)}')

    return redirect(url_for('agent.agent_list'))

# 确认绑定
@binding_bp.route('/confirm_binding/<int:binding_id>', methods=['POST'])
@login_required
def confirm_binding(binding_id):
    binding = Binding.query.get_or_404(binding_id)

    # 权限校验
    if current_user.id not in [binding.agent_id, binding.buyer_id]:
        flash('没有权限确认此绑定', 'danger')
        return redirect(url_for('binding.binding_detail', buyer_id=binding.buyer_id))

    # 状态校验
    if binding.status != 'pending':
        flash('该绑定已确认，无需重复操作', 'info')
        return redirect(url_for('binding.binding_detail', buyer_id=binding.buyer_id))

    # 更新状态
    binding.status = 'confirmed'
    db.session.commit()

    flash('绑定已确认成功', 'success')
    return redirect(url_for('binding.binding_detail', buyer_id=binding.buyer_id))

# 绑定详情
@binding_bp.route('/binding/detail/<int:buyer_id>')
@login_required
def binding_detail(buyer_id):
    binding = Binding.query.filter_by(
        agent_id=current_user.id,
        buyer_id=buyer_id
    ).first()

    if not binding:
        flash('未找到绑定信息', 'danger')
        return redirect(url_for('shopping.shopping_circle'))

    return render_template('binding_detail.html', binding=binding)