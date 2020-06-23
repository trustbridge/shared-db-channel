import logging
import random
from datetime import datetime

import requests
from libtrustbridge.repos.miniorepo import MinioRepo
from libtrustbridge.websub import repos
from libtrustbridge.websub.domain import Pattern
from botocore.exceptions import ClientError

from api import models
from api.app import db

logger = logging.getLogger(__name__)


class NewMessagesNotifyUseCase:
    """
    Query shared database in order to receive new messages directed
    to the endpoint and send notification for each message.
    """
    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    def __init__(self, receiver, channel_repo: MinioRepo, notifications_repo: repos.NotificationsRepo):
        self.channel_repo = channel_repo
        self.notifications_repo = notifications_repo
        self.receiver = receiver

    def execute(self):
        since = self.get_last_updated_at()
        if not since:
            logger.warning("No last updated_at, using now")
            since = datetime.utcnow()
            self.set_last_updated_at(since)

        messages = self.get_new_messages(receiver=self.receiver, since=since)
        use_case = PublishNewMessageUseCase(self.notifications_repo)
        for message in messages:
            logger.info('processing message: %s', message.id)
            # TODO error handling to be implemented
            use_case.publish(message)
            self.set_last_updated_at(message.updated_at)

    def set_last_updated_at(self, updated_at: datetime):
        updated_at_str = updated_at.strftime(self.TIMESTAMP_FORMAT)
        self.channel_repo.put_object(clean_path='updated_at', content_body=updated_at_str)

    def get_new_messages(self, receiver: str, since: datetime):
        messages = db.session.query(models.Message).filter(
            models.Message.payload['receiver'].as_string() == receiver,
            models.Message.updated_at > since
        ).order_by(models.Message.updated_at.asc()).all()
        return messages

    def get_last_updated_at(self):
        try:
            updated_at_str = self.channel_repo.get_object_content('updated_at').decode()
            return datetime.strptime(updated_at_str, self.TIMESTAMP_FORMAT)
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                logger.warning('updated_at not found')
            else:
                raise


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, pattern, expiration to the storage.
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
        pattern = Pattern(topic)
        subscriptions = self.subscriptions_repo.get_subscriptions_by_pattern(pattern)
        subscriptions_by_url = [s for s in subscriptions if s.callback_url == url]
        if not subscriptions_by_url:
            raise SubscriptionNotFound()
        self.subscriptions_repo.bulk_delete([pattern.to_key(url)])


class PostNotificationUseCase:
    """
    Base use case to send message for notification
    """

    def __init__(self, notification_repo: repos.NotificationsRepo):
        self.notifications_repo = notification_repo

    def publish(self, message: models.Message):
        topic = self.get_topic(message)
        job_payload = {
            'topic': topic,
            'content': {'id': message.id}
        }
        logger.info('publishing payload: %r', job_payload)
        self.notifications_repo.post_job(job_payload)

    @staticmethod
    def get_topic(message: models.Message):
        raise NotImplementedError


class PublishStatusChangeUseCase(PostNotificationUseCase):
    """
    Given message status changed
    message id should be sent for notification
    """

    @staticmethod
    def get_topic(message: models.Message):
        return f"{message.id}"


class PublishNewMessageUseCase(PostNotificationUseCase):
    """
    Given new message,
    message id should be posted for notification"""

    @staticmethod
    def get_topic(message: models.Message):
        jurisdiction = message.payload['receiver']
        return f"jurisdiction.{jurisdiction}"


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


class InvalidCallbackResponse(Exception):
    pass


class DeliverCallbackUseCase:
    """
    Is used by a callback deliverer worker

    Reads queue delivery_outbox_repo consisting of tasks in format:
        (url, message)

    Then such message should be either sent to this URL and the task is deleted
    or, in case of any error, not to be re-scheduled again
    (up to MAX_ATTEMPTS times)

    """

    MAX_ATTEMPTS = 3

    def __init__(self, delivery_outbox_repo: repos.DeliveryOutboxRepo, hub_url):
        self.delivery_outbox = delivery_outbox_repo
        self.hub_url = hub_url

    def execute(self):
        deliverable = self.delivery_outbox.get_job()
        if not deliverable:
            return

        queue_msg_id, payload = deliverable
        return self.process(queue_msg_id, payload)

    def process(self, queue_msg_id, job):
        subscribe_url = job['s']
        payload = job['payload']
        attempt = int(job.get('retry', 1))

        try:
            self._deliver_notification(subscribe_url, payload)
        except InvalidCallbackResponse as e:
            logger.exception(e)
            if attempt < self.MAX_ATTEMPTS:
                self._retry(subscribe_url, payload, attempt)

        self.delivery_outbox.delete(queue_msg_id)

    def _retry(self, subscribe_url, payload, attempt):
        logger.info("Delivery failed, re-schedule it")
        job = {'s': subscribe_url, 'payload': payload, 'retry': attempt + 1}
        self.delivery_outbox.post_job(job, delay_seconds=self._get_retry_time(attempt))

    def _deliver_notification(self, url, payload):
        """
        Send the payload to subscriber's callback url

        https://indieweb.org/How_to_publish_and_consume_WebSub
        https://www.w3.org/TR/websub/#x7-content-distribution
        """

        logger.info("Sending WebSub payload \n    %s to callback URL \n    %s", payload, url)
        header = {
            'Link': f'<{self.hub_url}>; rel="hub"'
        }
        resp = requests.post(url, json=payload, headers=header)
        if str(resp.status_code).startswith('2'):
            return

        raise InvalidCallbackResponse("Subscription url %s seems to be invalid, "
                                      "returns %s", url, resp.status_code)

    @staticmethod
    def _get_retry_time(attempt):
        """exponential back off with jitter"""
        base = 8
        max_retry = 100
        delay = min(base * 2 ** attempt, max_retry)
        jitter = random.uniform(0, delay / 2)
        return int(delay / 2 + jitter)
