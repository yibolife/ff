from app import db
from datetime import datetime

class Binding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending/confirmed/canceled

    # 关联用户
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='bindings_as_buyer')
    agent = db.relationship('User', foreign_keys=[agent_id], backref='bindings_as_agent')

    # 唯一约束：一个用户不能重复绑定同一个代购
    __table_args__ = (db.UniqueConstraint('buyer_id', 'agent_id', name='unique_buyer_agent'),)

    # 别名：模板用create_time访问
    @property
    def create_time(self):
        return self.created_at