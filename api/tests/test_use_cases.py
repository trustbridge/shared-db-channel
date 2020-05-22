from unittest import mock

from libtrustbridge.websub.repos import NotificationsRepo

from api.models import Message, MessageStatus
from api.use_cases import PublishStatusChangeUseCase


class TestPublishStatusChangeUseCase:
    def test_use_case__should_send_message_to_notification_queue(self):
        notifications_repo = mock.create_autospec(NotificationsRepo).return_value

        message = Message(id=24, status=MessageStatus.CONFIRMED, payload={'sender': 'CN'})
        PublishStatusChangeUseCase(notifications_repo).publish(message=message)

        notifications_repo.post_job.assert_called_once_with({
            'predicate': '24',
            'payload': {
                'id': 24
            }
        })
