from app import db
from datetime import datetime, date

class AgentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    itinerary = db.Column(db.Text, nullable=False)
    is_submitted = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 双向关联
    所属用户 = db.relationship(
        'User',
        backref=db.backref('agent_itinerary', uselist=False, lazy='joined')
    )

class ContactedTrip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_name = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    requirements = db.Column(db.Text)
    contact_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="已沟通")

    # 关联被联系的购物用户
    contact_user = db.relationship('User', foreign_keys=[contact_user_id], backref='contacted_by_trips')