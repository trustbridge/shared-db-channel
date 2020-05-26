import logging

from libtrustbridge.websub import repos
from libtrustbridge.websub.domain import Pattern

from api import models

logger = logging.getLogger(__name__)


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


class DispatchMessageToSubscribersUseCase:
    """
    Used by the callbacks spreader worker.

    This is the "fan-out" part of the WebSub,
    where each event dispatched
    to all the relevant subscribers.
    For each event (notification),
    it looks-up the relevant subscribers
    and dispatches a callback task
    so that they will be notified.

    There is a downstream delivery processor
    that actually makes the callback,
    it is insulated from this process
    by the delivery outbox message queue.

    """

    def __init__(
            self, notifications_repo: repos.NotificationsRepo,
            delivery_outbox_repo: repos.DeliveryOutboxRepo,
            subscriptions_repo: repos.SubscriptionsRepo):
        self.notifications = notifications_repo
        self.delivery_outbox = delivery_outbox_repo
        self.subscriptions = subscriptions_repo

    def execute(self):
        job = self.notifications.get_job()
        if not job:
            return
        return self.process(*job)

    def process(self, msg_id, payload):
        subscriptions = self._get_subscriptions(payload['topic'])

        content = payload['content']

        for subscription in subscriptions:
            if not subscription.is_valid:
                continue
            job = {
                's': subscription.callback_url,
                'payload': content,
            }
            logger.info("Scheduling notification of \n[%s] with the content \n%s", subscription.callback_url, content)
            self.delivery_outbox.post_job(job)

        self.notifications.delete(msg_id)

    def _get_subscriptions(self, topic):
        pattern = repos.Pattern(topic)
        subscribers = self.subscriptions.get_subscriptions_by_pattern(pattern)
        if not subscribers:
            logger.info("Nobody to notify about the topic %s", topic)
        return subscribers
