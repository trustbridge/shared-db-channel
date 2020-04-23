from datetime import datetime

from flask import url_for
from freezegun import freeze_time

from api.models import Message, MessageStatus


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
    assert response.json == {'id': 1}

    message = Message.query.order_by(Message.id.desc()).first()
    assert message.status == MessageStatus.CONFIRMED
    assert message.payload == message_data
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


def test_get_message__when_not_exist__should_return_404(client, db_session):
    response = client.get(url_for('views.get_message', id=123))
    assert response.status_code == 404


def test_get_message__when_missing_id__should_return_404(client, db_session):
    response = client.get('/messages/')
    assert response.status_code == 404


def test_get_message__when_exist__should_return_it(client, message):
    response = client.get(url_for('views.get_message', id=message.id))
    assert response.status_code == 200
    assert response.json == {
        'id': 42,
        'status': 'confirmed',
        'message': {
            'sender': 'AU'
        }
    }


def test_get_message__when_fields_provided__should_return_only_requested_fields(client, message):
    response = client.get(url_for('views.get_message', id=message.id) + '?fields=status')
    assert response.status_code == 200
    assert response.json == {
        'status': 'confirmed',
    }
