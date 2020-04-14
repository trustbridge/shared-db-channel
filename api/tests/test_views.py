from datetime import datetime

from flask import url_for
from freezegun import freeze_time

from api.models import Message


def test_index_view(client):
    response = client.get(url_for('views.index'))
    assert response.status_code == 200
    assert response.json == {'service': 'shared-db-channel'}


@freeze_time('2020-04-07 14:21:22.123456')
def test_post_message__when_posted__should_create_message_in_db(client, db_session):
    message_data = {
        "sender": "AU",
        "receiver": "CN",
        "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
        "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
    }
    response = client.post(url_for('views.post_message'), json=message_data)
    assert response.status_code == 201
    assert response.json == message_data

    message = Message.query.order_by(Message.id.desc()).first()
    assert message.sender == 'AU'
    assert message.receiver == 'CN'
    assert message.subject == 'AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX'
    assert message.obj == 'QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n'
    assert message.predicate == 'UN.CEFACT.Trade.CertificateOfOrigin.created'
    assert message.created_at == datetime(2020, 4, 7, 14, 21, 22, 123456)


def test_post_message__when_missing_field__should_return_400(client):
    response = client.post(url_for('views.post_message'), json={})
    assert response.status_code == 400
    assert response.json == {
        'obj': ['Missing data for required field.'],
        'predicate': ['Missing data for required field.'],
        'receiver': ['Missing data for required field.'],
        'sender': ['Missing data for required field.'],
        'subject': ['Missing data for required field.']
    }
