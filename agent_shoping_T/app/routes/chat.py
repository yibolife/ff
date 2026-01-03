from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.binding import Binding

chat_bp = Blueprint('chat', __name__)


# 聊天房间页面（通过绑定ID进入）
@chat_bp.route('/room/<int:binding_id>')
@login_required
def chat_room(binding_id):
    # 1. 校验绑定是否存在，且当前用户是代购/买家
    binding = Binding.query.get_or_404(binding_id)
    if current_user.id not in [binding.agent_id, binding.buyer_id]:
        flash('您无权进入该聊天房间', 'danger')
        return redirect(url_for('binding.binding_list'))

    # 2. 获取聊天对方信息
    if current_user.id == binding.agent_id:
        opponent = binding.buyer  # 代购的聊天对象是买家
    else:
        opponent = binding.agent  # 买家的聊天对象是代购

    # 3. 房间ID用绑定ID的字符串形式（统一格式）
    room_id = str(binding_id)

    return render_template(
        'chat/chat_room.html',
        room_id=room_id,
        current_user=current_user,
        opponent=opponent,
        binding=binding
    )


# 获取聊天历史（API接口，可选）
@chat_bp.route('/history/<int:binding_id>')
@login_required
def chat_history(binding_id):
    from app.models.chat import ChatMessage
    # 校验权限
    binding = Binding.query.get_or_404(binding_id)
    if current_user.id not in [binding.agent_id, binding.buyer_id]:
        flash('无权查看该聊天记录', 'danger')
        return redirect(url_for('binding.binding_list'))

    # 查询历史消息
    history = ChatMessage.query.filter_by(room_id=str(binding_id)).order_by(ChatMessage.created_at.asc()).all()
    return {
        'code': 200,
        'data': [{
            'sender': msg.sender_name,
            'content': msg.content,
            'time': msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for msg in history]
    }