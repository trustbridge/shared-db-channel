from datetime import datetime
from urllib.parse import urlencode

import pytest
from flask import url_for
from freezegun import freeze_time
from libtrustbridge.websub.domain import Pattern

from api.models import Message, MessageStatus


def test_index_view(client):
    response = client.get(url_for('views.index'))
    assert response.status_code == 200
    assert response.json == {'service': 'shared-db-channel'}


@pytest.mark.usefixtures("db_session", "client_class", "clean_notifications_repo")
class TestPostMessage:
    message_data = {
        "sender": "AU",
        "receiver": "CN",
        "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
        "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
        "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
    }

    @freeze_time('2020-04-07 14:21:22.123456')
    def test_post_message__when_posted__should_create_message_in_db(self):
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        assert response.status_code == 201
        assert response.json == {'id': 1}

        message = Message.query.order_by(Message.id.desc()).first()
        assert message.status == MessageStatus.CONFIRMED
        assert message.payload == self.message_data
        assert message.created_at == datetime(2020, 4, 7, 14, 21, 22, 123456)

    def test_post_message__when_missing_field__should_return_400(self):
        response = self.client.post(url_for('views.post_message'), json={})
        assert response.status_code == 400
        assert response.json == {
            'obj': ['Missing data for required field.'],
            'predicate': ['Missing data for required field.'],
            'receiver': ['Missing data for required field.'],
            'sender': ['Missing data for required field.'],
            'subject': ['Missing data for required field.']
        }

    def test_message__when_posted__should_return_websub_link_headers(self):
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        message_id = response.json['id']
        assert 'Link' in response.headers
        assert response.headers['Link'] == ('<http://localhost/subscriptions>; rel="hub", '
                                            f'<message.{message_id}.status>; rel="self"')

    def test_message__when_posted__should_publish_notification(self):
        response = self.client.post(url_for('views.post_message'), json=self.message_data)
        message_id = response.json['id']
        assert self.notifications_repo.get_job()[1] == {'content': {'id': message_id}, 'topic': 'jurisdiction.CN'}


@pytest.mark.usefixtures("db_session", "client_class")
class TestGetMessage:
    def test_get_message__when_not_exist__should_return_404(self):
        response = self.client.get(url_for('views.get_message', id=123))
        assert response.status_code == 404

    def test_get_message__when_missing_id__should_return_404(self):
        response = self.client.get('/messages/')
        assert response.status_code == 404

    def test_get_message__when_exist__should_return_it(self, message):
        response = self.client.get(url_for('views.get_message', id=message.id))
        assert response.status_code == 200
        assert response.json == {
            'id': 42,
            'status': 'confirmed',
            'message': {
                'sender': 'AU'
            }
        }

    def test_get_message__when_fields_provided__should_return_only_requested_fields(self, message):
        response = self.client.get(url_for('views.get_message', id=message.id) + '?fields=status')
        assert response.status_code == 200
        assert response.json == {
            'status': 'confirmed',
        }


@pytest.mark.usefixtures("client_class", )
class TestUpdateMessageStatus:
    @pytest.fixture(autouse=True)
    def message(self, request, db_session):
        self.db_session = db_session
        self.message = Message(payload={"sender": "AU"})
        self.db_session.add(self.message)
        self.db_session.commit()

    def test_put__with_new_status__should_update_status(self):
        response = self.client.put(
            url_for('views.update_message_status', id=self.message.id),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode({'status': 'revoked'})
        )
        assert response.status_code == 200, response.json
        assert response.json['status'] == 'revoked'

        self.db_session.refresh(self.message)
        assert self.message.status == MessageStatus.REVOKED

    def test_put__with_wrong_status__should_return_400(self):
        response = self.client.put(
            url_for('views.update_message_status', id=self.message.id),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode({'status': 'WRONG-STATUS'})
        )
        assert response.status_code == 400, response.json
        assert response.json == {'status': ['Invalid enum value WRONG-STATUS']}

    def test_put__when_missing_message__should_return_404(self):
        response = self.client.put(
            url_for('views.update_message_status', id=444),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode({'status': 'revoked'})
        )
        assert response.status_code == 404, response.json


@pytest.mark.usefixtures("client_class", "clean_subscriptions_repo")
class TestSubscriptions:
    def test_post__with_subscribe_mode__should_subscribe(self):
        params = {
            'hub.mode': 'subscribe',
            'hub.callback': 'https://callback.url/1',
            'hub.topic': 'aa.bb.cc',
        }
        response = self.client.post(
            url_for('views.subscriptions'),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode(params)
        )
        assert response.status_code == 202, response.json
        assert self.subscriptions_repo.get_subscriptions_by_pattern(Pattern('aa.bb.cc'))

    def test_post__with_unsubscribe_mode__should_unsubscribe(self):
        self.subscriptions_repo.subscribe_by_pattern(Pattern('aa.bb.cc'), 'https://callback.url/1', 30)
        assert self.subscriptions_repo.get_subscriptions_by_pattern(Pattern('aa.bb.cc'))

        params = {
            'hub.mode': 'unsubscribe',
            'hub.callback': 'https://callback.url/1',
            'hub.topic': 'aa.bb.cc',
        }
        response = self.client.post(
            url_for('views.subscriptions'),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode(params)
        )
        assert response.status_code == 202, response.json
        assert not self.subscriptions_repo.get_subscriptions_by_pattern(Pattern('aa.bb.cc'))

    def test_post_with_wrong_params__should_return_error(self):
        params = {}
        response = self.client.post(
            url_for('views.subscriptions'),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode(params)
        )
        assert response.status_code == 400, response.json
        assert response.json == {
            'hub.callback': ['Missing data for required field.'],
            'hub.mode': ['Missing data for required field.'],
            'hub.topic': ['Missing data for required field.'],
        }


@pytest.mark.usefixtures("client_class", "clean_subscriptions_repo")
class TestSubscriptionsByJurisdiction:
    def test_post__with_subscribe_mode__should_subscribe_to_all_messages_by_jurisdiction(self):
        params = {
            'hub.mode': 'subscribe',
            'hub.callback': 'https://callback.url/1',
            'hub.topic': 'AU',
        }
        response = self.client.post(
            url_for('views.subscriptions_by_jurisdiction'),
            mimetype='application/x-www-form-urlencoded',
            data=urlencode(params)
        )
        assert response.status_code == 202, response.json
        assert self.subscriptions_repo.get_subscriptions_by_pattern(Pattern('jurisdiction.AU'))
