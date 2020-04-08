from datetime import datetime

from api.app import db


class Message(db.Model):
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(8))
    receiver = db.Column(db.String(8))
    subject = db.Column(db.String(1024))
    obj = db.Column(db.String(1024))
    predicate = db.Column(db.String(1024))

    def __repr__(self):
        return f'<Message from:{self.sender} to:{self.receiver}> subj:{self.subject}'
