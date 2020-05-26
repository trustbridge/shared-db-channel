import random
from unittest import mock, TestCase

import responses
from libtrustbridge.websub.repos import NotificationsRepo, DeliveryOutboxRepo, SubscriptionsRepo

from api.models import Message, MessageStatus
from api.use_cases import (
    PublishStatusChangeUseCase, DispatchMessageToSubscribersUseCase, DeliverCallbackUseCase
)


class TestPublishStatusChangeUseCase:
    def test_use_case__should_send_message_to_notification_queue(self):
        notifications_repo = mock.create_autospec(NotificationsRepo).return_value

        message = Message(id=24, status=MessageStatus.CONFIRMED, payload={'sender': 'CN'})
        PublishStatusChangeUseCase(notifications_repo).publish(message=message)

        notifications_repo.post_job.assert_called_once_with({
            'topic': 'message.24.status',
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
