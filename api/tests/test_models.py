from datetime import datetime

from freezegun import freeze_time

from api.models import MessageStatus, Message


@freeze_time('2020-04-07 14:21:22.123456')
def test_message__can_be_created(db_session):
    message = Message(id=42, payload={"sender": "AU"})
    db_session.add(message)
    db_session.commit()
    message = db_session.query(Message).get(42)

    assert message.status == MessageStatus.CONFIRMED
    assert message.payload == {"sender": "AU"}
    assert message.created_at == datetime(2020, 4, 7, 14, 21, 22, 123456)

