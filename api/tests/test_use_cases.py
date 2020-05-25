from unittest import mock, TestCase

from libtrustbridge.websub.repos import NotificationsRepo, DeliveryOutboxRepo, SubscriptionsRepo

from api.models import Message, MessageStatus
from api.use_cases import PublishStatusChangeUseCase, DispatchMessageToSubscribersUseCase


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
