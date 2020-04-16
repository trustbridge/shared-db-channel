import enum
from datetime import datetime

from api.app import db


class MessageStatus(enum.Enum):
    RECEIVED = 'received'
    CONFIRMED = 'confirmed'
    REVOKED = 'revoked'
    UNDELIVERABLE = 'undeliverable'


class Message(db.Model):
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())
    status = db.Column(
        db.Enum(MessageStatus, values_callable=lambda enum: [e.value for e in enum], native_enum=False),
        default=MessageStatus.CONFIRMED)
    id = db.Column(db.Integer, primary_key=True)
    payload = db.Column(db.JSON)

    def __repr__(self):
        return f'<Message id:{self.id}>'
