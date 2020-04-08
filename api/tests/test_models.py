from datetime import datetime

from freezegun import freeze_time

from api import models


@freeze_time('2020-04-07 14:21:22.123456')
def test_message__can_be_created(db_session):
    db_session.add(models.Message(id=42, sender='AU'))
    db_session.commit()
    message = db_session.query(models.Message).get(42)
    assert message.sender == 'AU'
    assert message.created_at == datetime(2020, 4, 7, 14, 21, 22, 123456)

