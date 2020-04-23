from datetime import datetime

from api.models import MessageStatus, Message


def test_message__can_be_created(db_session, message):
    created = db_session.query(Message).get(message.id)

    assert created.status == MessageStatus.CONFIRMED
    assert created.payload == message.payload
    assert created.created_at == datetime(2020, 4, 7, 14, 21, 22, 123456)

