from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Binding, User
from app.forms.binding_forms import ConfirmBindingForm  # 导入确认绑定表单

from app.forms.binding_forms import UnbindForm  # 需创建空表单类（仅用于 CSRF 保护）

binding_bp = Blueprint('binding', __name__)

# ------------------------------
# 1. 代购用户绑定买家（代购发起）
# ------------------------------
@binding_bp.route('/bind/buyer/<int:buyer_id>')
@login_required
def bind_buyer(buyer_id):
    if not current_user.is_agent:
        flash('只有代购用户可以发起绑定', 'danger')
        return redirect(url_for('shopping.shopping_info'))

    # 校验买家是否存在
    buyer_user = User.query.get_or_404(buyer_id)
    if buyer_user.is_agent:
        flash('不能绑定代购用户为买家', 'danger')
        return redirect(url_for('shopping.shopping_info'))

    # 检查是否已绑定
    existing_binding = Binding.query.filter_by(
        agent_id=current_user.id,
        buyer_id=buyer_id
    ).first()

    if existing_binding:
        flash(f'已与买家「{buyer_user.username}」绑定', 'info')
        # 跳转到按 buyer_id 查询的详情页
        return redirect(url_for('binding.binding_detail_by_buyer', buyer_id=buyer_id))

    # 创建绑定（状态：待确认）
    new_binding = Binding(
        agent_id=current_user.id,
        buyer_id=buyer_id,
        status='pending'
    )
    db.session.add(new_binding)
    try:
        db.session.commit()
        flash(f'绑定请求已发送给买家「{buyer_user.username}」，等待对方确认', 'success')
    except Exception as e:
        db.session.rollback()
        flash('绑定请求发送失败，请重试', 'danger')
        print(f'绑定失败：{str(e)}')

    return redirect(url_for('binding.binding_detail_by_buyer', buyer_id=buyer_id))

# ------------------------------
# 2. 普通用户绑定代购（买家发起）
# ------------------------------
@binding_bp.route('/bind_agent/<int:agent_id>')
@login_required
def bind_agent(agent_id):
    # 权限校验：仅普通用户可绑定代购
    if current_user.is_agent:
        flash('代购用户不能绑定其他代购', 'danger')
        return redirect(url_for('agent.agent_list'))

    # 校验代购是否存在且有效
    agent_user = User.query.get_or_404(agent_id)
    if not agent_user.is_agent:
        flash('无效的代购用户（该用户未开通代购权限）', 'danger')
        return redirect(url_for('agent.agent_list'))

    # 检查是否已绑定
    existing_binding = Binding.query.filter_by(
        buyer_id=current_user.id,
        agent_id=agent_id
    ).first()
    if existing_binding:
        flash(f'您已与代购「{agent_user.username}」绑定，无需重复操作', 'warning')
        return redirect(url_for('agent.agent_list'))

    # 创建绑定（状态：待确认）
    new_binding = Binding(
        buyer_id=current_user.id,
        agent_id=agent_id,
        status='pending'
    )
    db.session.add(new_binding)
    try:
        db.session.commit()
        flash(f'绑定请求已发送给代购「{agent_user.username}」，等待对方确认', 'success')
    except Exception as e:
        db.session.rollback()
        flash('绑定失败，请重试', 'danger')
        print(f'绑定失败：{str(e)}')

    return redirect(url_for('agent.agent_list'))

# ------------------------------
# 3. 确认绑定（唯一实现，带 CSRF 保护）
# ------------------------------
@binding_bp.route('/confirm_binding/<int:binding_id>', methods=['GET', 'POST'])
@login_required
def confirm_binding(binding_id):
    form = ConfirmBindingForm()  # 实例化表单，启用 CSRF 保护
    binding = Binding.query.get_or_404(binding_id)

    # 表单验证通过（携带有效 CSRF 令牌）
    if form.validate_on_submit():
        # 权限校验：仅绑定的代购或买家可确认
        if current_user.id not in [binding.agent_id, binding.buyer_id]:
            flash('没有权限确认此绑定', 'danger')
            # 跳转到按 binding_id 查询的通用详情页
            return redirect(url_for('binding.binding_detail_by_id', binding_id=binding.id))

        # 状态校验：仅待确认状态可操作
        if binding.status != 'pending':
            flash('该绑定已确认或失效，无需重复操作', 'info')
            return redirect(url_for('binding.binding_detail_by_id', binding_id=binding.id))

        # 更新绑定状态为已确认
        binding.status = 'confirmed'
        db.session.commit()

        # 区分用户身份提示
        if current_user.id == binding.agent_id:
            buyer = User.query.get(binding.buyer_id)
            flash(f'已确认与买家「{buyer.username}」的绑定', 'success')
        else:
            agent = User.query.get(binding.agent_id)
            flash(f'已确认与代购「{agent.username}」的绑定', 'success')

        return redirect(url_for('binding.binding_detail_by_id', binding_id=binding.id))

    # GET 请求：渲染确认页面（携带表单和 CSRF 令牌）
    return render_template(
        'confirm_binding.html',
        form=form,
        binding=binding
    )

# ------------------------------
# 4. 绑定详情（按 buyer_id 查询，代购视角）→ 唯一函数名
# ------------------------------
@binding_bp.route('/binding/detail/<int:buyer_id>')
@login_required
def binding_detail_by_buyer(buyer_id):
    # 仅代购用户可通过 buyer_id 查询
    if not current_user.is_agent:
        flash('只有代购用户可查看该绑定详情', 'danger')
        return redirect(url_for('shopping.shopping_circle'))

    # 查询当前代购与该买家的绑定
    binding = Binding.query.filter_by(
        agent_id=current_user.id,
        buyer_id=buyer_id
    ).first()

    if not binding:
        flash('未找到与该买家的绑定信息', 'danger')
        return redirect(url_for('shopping.shopping_circle'))

    # 关联查询代购和买家信息（供模板使用）
    binding.agent = User.query.get(binding.agent_id)
    binding.buyer = User.query.get(binding.buyer_id)

    # 实例化表单（用于详情页确认按钮的 CSRF 令牌）
    form = ConfirmBindingForm()

    return render_template('binding_detail.html', binding=binding, form=form)

# ------------------------------
# 5. 绑定详情（按 binding_id 查询，通用视角）→ 唯一函数名
# ------------------------------
@binding_bp.route('/binding-detail/<int:binding_id>')
@login_required
def binding_detail_by_id(binding_id):
    # 查询绑定记录 + 关联用户信息（避免模板 N+1 查询）
    binding = Binding.query.get_or_404(binding_id)
    binding.agent = User.query.get(binding.agent_id)
    binding.buyer = User.query.get(binding.buyer_id)

    # 权限校验：仅绑定的代购或买家可查看
    if current_user.id not in [binding.agent_id, binding.buyer_id]:
        flash('没有权限查看该绑定详情', 'danger')
        return redirect(url_for('binding.binding_list'))

    # 实例化表单（用于详情页确认按钮的 CSRF 令牌）
    form = ConfirmBindingForm()

    return render_template('binding_detail.html', binding=binding, form=form)

# ------------------------------
# 6. 我的绑定列表（显示当前用户所有绑定）
# ------------------------------
@binding_bp.route('/binding-list')
@login_required
def binding_list():
    # 查询当前用户作为代购或买家的所有绑定（按时间倒序）
    bindings = Binding.query.filter(
        (Binding.agent_id == current_user.id) | (Binding.buyer_id == current_user.id)
    ).order_by(Binding.created_at.desc()).all()

    # 关联查询每个绑定的用户信息（供模板渲染）
    for binding in bindings:
        binding.agent = User.query.get(binding.agent_id)
        binding.buyer = User.query.get(binding.buyer_id)

    # 实例化表单（用于列表页确认按钮的 CSRF 令牌）
    form = ConfirmBindingForm()

    return render_template('binding_list.html', bindings=bindings, form=form)

# 解除绑定路由（与模板 form 对应）
# ------------------------------
@binding_bp.route('/unbind/<int:binding_id>', methods=['POST'])
@login_required
def unbind(binding_id):
    form = UnbindForm()  # 空表单，仅用于 CSRF 验证
    binding = Binding.query.get_or_404(binding_id)

    # 1. CSRF 验证 + 权限校验
    if form.validate_on_submit():
        # 仅绑定的代购或买家可解除绑定
        if current_user.id not in [binding.agent_id, binding.buyer_id]:
            flash('没有权限解除此绑定', 'danger')
            return redirect(url_for('agent.contacted_trips'))

        # 2. 执行解除绑定（删除绑定记录）
        try:
            # 先查询买家/代购信息（Python 正确的容错写法）
            if current_user.id == binding.agent_id:
                buyer = User.query.get(binding.buyer_id)
                # Python 容错：用 or 替代 Jinja2 的 |default
                buyer_name = buyer.username if (buyer and buyer.username) else "未知用户"
            else:
                agent = User.query.get(binding.agent_id)
                agent_name = agent.username if (agent and agent.username) else "未知代购"

            # 删除绑定记录
            db.session.delete(binding)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            # 异常提示：直接打印错误，避免嵌套变量导致新问题
            flash(f'解除绑定失败：{str(e)}', 'danger')

    return redirect(url_for('agent.contacted_trips'))  # 解除后返回已联系行程页面

@binding_bp.route('/bind/buyer/direct-confirm/<int:buyer_id>')
@login_required
def bind_buyer_direct_confirm(buyer_id):
    # 权限校验：仅代购用户可发起
    if not current_user.is_agent:
        flash('只有代购用户可以发起绑定', 'danger')
        return redirect(url_for('shopping.shopping_info'))

    # 校验买家是否存在
    buyer_user = User.query.get_or_404(buyer_id)
    if buyer_user.is_agent:
        flash('不能绑定代购用户为买家', 'danger')
        return redirect(url_for('shopping.shopping_info'))

    # 检查是否已存在绑定（代购-买家唯一）
    existing_binding = Binding.query.filter_by(
        agent_id=current_user.id,
        buyer_id=buyer_id
    ).first()

    if existing_binding:
        flash(f'已与买家「{buyer_user.username}」绑定', 'info')
        # 核心修改1：已绑定则跳转至 contacted_trips
        return redirect(url_for('agent.contacted_trips'))

    # 核心修改：创建绑定并直接设置为 confirmed 状态（无需 pending）
    new_binding = Binding(
        agent_id=current_user.id,
        buyer_id=buyer_id,
        status='confirmed'  # 直接确认，跳过待确认
    )
    db.session.add(new_binding)
    try:
        db.session.commit()

        # 核心修改2：绑定成功后跳转至 contacted_trips
        return redirect(url_for('agent.contacted_trips'))
    except Exception as e:
        db.session.rollback()
        flash('绑定请求发送失败，请重试', 'danger')
        print(f'绑定失败：{str(e)}')
        # 绑定失败仍跳转至 shopping-circle，方便重试
        return redirect(url_for('shopping.shopping_circle'))
