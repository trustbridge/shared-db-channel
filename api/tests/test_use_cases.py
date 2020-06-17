import random
from datetime import datetime
from unittest import mock, TestCase

import pytest
import responses
from freezegun import freeze_time
from libtrustbridge.websub.repos import NotificationsRepo, DeliveryOutboxRepo, SubscriptionsRepo

from api.models import Message, MessageStatus
from api.use_cases import (
    PublishStatusChangeUseCase, DispatchMessageToSubscribersUseCase, DeliverCallbackUseCase, NewMessagesNotifyUseCase
)


class TestGetNewMessagesUseCase:
    @pytest.fixture(autouse=True)
    def message(self, request, db_session, clean_channel_repo, clean_notifications_repo):
        self.db_session = db_session
        self.message = Message(payload={"receiver": "AU"})
        with freeze_time('2020-06-17 12:04:01.111111'):
            messages = [
                self.message,
                Message(payload={"receiver": "AU"}),
                Message(payload={"receiver": "SG"}),
            ]
            for m in messages:
                self.db_session.add(m)

            self.db_session.commit()

        with freeze_time('2020-06-17 12:04:03.111111'):
            messages = [
                Message(payload={"receiver": "SG"}),
            ]
            for m in messages:
                self.db_session.add(m)

            self.message.status = MessageStatus.REVOKED
            self.db_session.commit()

        self.channel_repo = clean_channel_repo
        self.notifications_repo = clean_notifications_repo
        self.use_case = NewMessagesNotifyUseCase('AU', clean_channel_repo, clean_notifications_repo)

    def test_get_new_messages__when_available__should_return_them(self):
        now = datetime(2020, 6, 17, 12, 4, 1, 222222)
        messages = self.use_case.get_new_messages(receiver='AU', since=now)
        assert len(messages) == 1
        assert messages[0].updated_at >= now
        assert messages[0].id == self.message.id

    def test_set_last_updated__should_set_timestamp_into_channel_repo(self):
        updated_at = datetime(2020, 6, 17, 11, 34, 56, 123456)
        self.use_case.set_last_updated_at(updated_at)
        assert self.use_case.get_last_updated_at() == updated_at
        assert self.channel_repo.get_object_content('updated_at') == b'2020-06-17T11:34:56.123456'

    def test_get_last_updated_at__when_not_available__should_return_none(self):
        assert self.use_case.get_last_updated_at() is None

    def test_execute__for_each_new_message__should_publish_notification(self):
        now = datetime(2020, 6, 17, 12, 4, 1, 222222)
        self.use_case.set_last_updated_at(now)
        self.use_case.execute()
        notification = self.notifications_repo.get_job()
        assert notification and notification[1] == {'content': {'id': 1}, 'topic': 'jurisdiction.AU'}
        assert not self.notifications_repo.get_job()

    def test_execute__when_no_last_updated_at__should_use_now(self):
        with mock.patch('api.use_cases.datetime') as mocked_datetime:
            mocked_datetime.utcnow.return_value = datetime(2020, 6, 17, 12, 1, 1, 222222)
            self.use_case.execute()
        notification = self.notifications_repo.get_job()
        notification2 = self.notifications_repo.get_job()
        assert notification and notification[1] == {'content': {'id': 1}, 'topic': 'jurisdiction.AU'}
        assert notification2 and notification2[1] == {'content': {'id': 2}, 'topic': 'jurisdiction.AU'}
        assert not self.notifications_repo.get_job()


class TestPublishStatusChangeUseCase:
    def test_use_case__should_send_message_to_notification_queue(self):
        notifications_repo = mock.create_autospec(NotificationsRepo).return_value

        message = Message(id=24, status=MessageStatus.CONFIRMED, payload={'sender': 'CN'})
        PublishStatusChangeUseCase(notifications_repo).publish(message=message)

        notifications_repo.post_job.assert_called_once_with({
            'topic': '24',
            'content': {
                'id': 24
            }
        })


class TestDispatchMessageToSubscribersUseCase(TestCase):
    def setUp(self):
        self.notifications_repo = mock.create_autospec(NotificationsRepo).return_value
        self.notifications_repo.get_job.return_value = (
            'msg_id', {'topic': 'message.24.status', 'content': {'id': 24}}
        )
        self.subscriptions_repo = mock.create_autospec(SubscriptionsRepo).return_value
        self.subscription1 = mock.Mock(callback_url='http://callback.url/1')
        self.subscription2 = mock.Mock(callback_url='http://callback.url/2')
        self.subscriptions_repo.get_subscriptions_by_pattern.return_value = {
            self.subscription1,
            self.subscription2,
        }
        self.delivery_outbox_repo = mock.create_autospec(DeliveryOutboxRepo).return_value

        self.use_case = DispatchMessageToSubscribersUseCase(
            self.notifications_repo, self.delivery_outbox_repo, self.subscriptions_repo
        )

    def test_use_case__given_notification__should_post_job_to_outbox_for_each_related_subscribers(self):
        self.use_case.execute()

        calls = self.delivery_outbox_repo.mock_calls
        assert mock.call.post_job({'s': 'http://callback.url/1', 'payload': {'id': 24}}) in calls
        assert mock.call.post_job({'s': 'http://callback.url/2', 'payload': {'id': 24}}) in calls

        assert self.subscriptions_repo.get_subscriptions_by_pattern.assert_called_once_with

    def test_use_case__when_no_subscribers_should_not_post(self):
        self.subscriptions_repo.get_subscriptions_by_pattern.return_value = set()

        self.use_case.execute()

        assert not self.delivery_outbox_repo.called

    def test_use_case__when_no_notifications__should_not_post(self):
        self.notifications_repo.get_job.return_value = False
        self.use_case.execute()

        assert not self.delivery_outbox_repo.called

    def test_use_case_when_subscription_not_valid__should_not_post_it(self):
        self.subscription1.is_valid = False
        self.use_case.execute()
        self.delivery_outbox_repo.post_job.assert_called_once_with({'s': 'http://callback.url/2', 'payload': {'id': 24}})


class TestDeliverCallbackUseCase(TestCase):
    def setUp(self):
        self.job = {'s': 'http://callback.url/1', 'payload': {'id': 55}}

        self.delivery_outbox_repo = mock.create_autospec(DeliveryOutboxRepo).return_value
        self.delivery_outbox_repo.get_job.return_value = 'queue_id', self.job

        self.use_case = DeliverCallbackUseCase(self.delivery_outbox_repo, 'https://channel.url/hub')
        random.seed(300)

    @responses.activate
    def test_use_case__given_deliverable__should_send_request(self):
        responses.add(responses.POST, 'http://callback.url/1', status=202)

        self.use_case.execute()
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert request.url == 'http://callback.url/1'
        assert request.headers['Link'] == '<https://channel.url/hub>; rel="hub"'
        assert request.body == b'{"id": 55}'
        assert not self.delivery_outbox_repo.post_job.called
        self.delivery_outbox_repo.delete.assert_called_once_with('queue_id')

    @responses.activate
    def test_use_case__when_callback_not_valid__should_retry(self):
        responses.add(responses.POST, 'http://callback.url/1', status=400)

        self.use_case.execute()
        new_job = {'payload': {'id': 55}, 's': 'http://callback.url/1', 'retry': 2}
        self.delivery_outbox_repo.post_job.assert_called_once_with(new_job, delay_seconds=12)
        self.delivery_outbox_repo.delete.assert_called_once_with('queue_id')

    @responses.activate
    def test_use_case__when_max_retry_attempts_reached__should_not_retry(self):
        self.job['retry'] = 3
        responses.add(responses.POST, 'http://callback.url/1', status=400)

        self.use_case.execute()
        self.delivery_outbox_repo.delete.assert_called_once_with('queue_id')
        assert not self.delivery_outbox_repo.post_job.called
