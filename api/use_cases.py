from libtrustbridge.websub import repos
from libtrustbridge.websub.domain import Pattern

from api import models


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, predicate(pattern), expiration to the storage.
    """

    def __init__(self, subscriptions_repo: repos.SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    def execute(self, url, topic, expiration=None):
        # this operation deletes all previous subscription for given url and pattern
        # and replaces them with new one. Techically it's create or update operation

        self.subscriptions_repo.subscribe_by_pattern(Pattern(topic), url, expiration)


class SubscriptionNotFound(Exception):
    pass


class SubscriptionDeregisterUseCase:
    """
    Used by the subscription API

    on user's request removes the subscription to given url for given pattern
    """

    def __init__(self, subscriptions_repo: repos.SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    def execute(self, url, topic):
        pattern = Pattern(predicate=topic)
        subscriptions = self.subscriptions_repo.get_subscriptions_by_pattern(pattern)
        subscriptions_by_url = [s for s in subscriptions if s.callback_url == url]
        if not subscriptions_by_url:
            raise SubscriptionNotFound()
        self.subscriptions_repo.bulk_delete([pattern.to_key(url)])


class PublishStatusChangeUseCase:
    """
    Given message status changed
    message id should be sent for notification
    """

    def __init__(self, notification_repo: repos.NotificationsRepo):
        self.notifications_repo = notification_repo

    def publish(self, message: models.Message):
        job_payload = {
            'topic': f"message.{message.id}.status",
            'content': {'id': message.id}
        }
        self.notifications_repo.post_job(job_payload)
