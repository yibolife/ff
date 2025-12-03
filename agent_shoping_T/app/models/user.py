from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    is_agent = db.Column(db.Boolean, nullable=True)  # True:代购, False:非代购
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联关系
    agent_info = db.relationship('AgentInfo', backref='user', lazy=True, uselist=False)
    shopping_info = db.relationship('ShoppingInfo', backref='user', lazy=True)
    shopping_circle = db.relationship('ShoppingCircle', backref='user', lazy=True, uselist=False)

    # 作为买家的绑定记录
    buyer_bindings = db.relationship(
        'Binding',
        foreign_keys='Binding.buyer_id',
        backref='buyer_user',
        lazy='dynamic'
    )

    # 作为代购的绑定记录
    agent_bindings = db.relationship(
        'Binding',
        foreign_keys='Binding.agent_id',
        backref='agent_user',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<User {self.username}, (phone: {self.phone})>"