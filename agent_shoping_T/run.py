from app import create_app, socketio  # 保留原有导入
import eventlet

eventlet.monkey_patch()  # eventlet异步补丁

# 关键修复：导入SocketIO核心方法
from flask_socketio import emit, join_room  # 新增这行！！！

# 创建app实例（默认开发环境）
app = create_app(config_name='production')


# --------------------------
# SocketIO聊天事件（核心逻辑）
# --------------------------
@socketio.on('join_chat')  # 客户端加入聊天房间
def handle_join_chat(data):
    from app.models.chat import ChatMessage
    from flask_login import current_user
    import datetime

    room_id = data['room_id']  # 聊天房间ID（绑定ID）
    # 权限校验：仅绑定的代购/买家可加入
    if not current_user.is_authenticated:
        emit('chat_error', {'msg': '请先登录'})
        return

    # 加入房间（依赖join_room方法）
    join_room(room_id)
    # 发送系统欢迎消息
    emit('chat_message', {
        'sender': '系统',
        'content': f'{current_user.username}已加入聊天',
        'time': datetime.datetime.now().strftime("%H:%M:%S")
    }, room=room_id)


@socketio.on('send_message')  # 客户端发送消息
def handle_send_message(data):
    from app import db
    from app.models.chat import ChatMessage
    from flask_login import current_user
    import datetime

    room_id = data['room_id']
    content = data.get('content', '').strip()

    # 基础校验
    if not current_user.is_authenticated:
        emit('chat_error', {'msg': '请先登录'})
        return
    if not content:
        emit('chat_error', {'msg': '消息内容不能为空'})
        return

    # 1. 构造消息数据
    message_data = {
        'sender': current_user.username,
        'sender_id': current_user.id,
        'content': content,
        'time': datetime.datetime.now().strftime("%H:%M:%S"),
        'room_id': room_id
    }

    # 2. 持久化到数据库
    try:
        chat_msg = ChatMessage(
            room_id=room_id,
            sender_id=current_user.id,
            sender_name=current_user.username,
            content=content,
            created_at=datetime.datetime.now()
        )
        db.session.add(chat_msg)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        emit('chat_error', {'msg': '消息保存失败'})
        print(f'消息持久化失败：{str(e)}')
        return

    # 3. 广播消息到房间内所有用户
    emit('chat_message', message_data, room=room_id)


@socketio.on('load_history')  # 加载历史消息
def handle_load_history(data):
    from app.models.chat import ChatMessage
    room_id = data['room_id']

    # 查询该房间的历史消息（按时间升序）
    history_msgs = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.created_at.asc()).all()
    # 格式化返回
    history_data = [{
        'sender': msg.sender_name,
        'sender_id': msg.sender_id,
        'content': msg.content,
        'time': msg.created_at.strftime("%H:%M:%S"),
        'room_id': msg.room_id
    } for msg in history_msgs]

    emit('history_messages', history_data)


if __name__ == '__main__':
    # 用socketio.run代替app.run
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=False)