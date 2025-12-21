from app import db
from datetime import datetime

class ChatMessage(db.Model):
    """聊天消息模型（关联绑定ID=房间ID）"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), nullable=False, comment='聊天房间ID（=绑定ID）')
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='发送者ID')
    sender_name = db.Column(db.String(20), nullable=False, comment='发送者昵称')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='发送时间')

    # 关联发送者
    sender = db.relationship('User', backref='chat_messages')

    def __repr__(self):
        return f"<ChatMessage {self.room_id} - {self.sender_name}>"