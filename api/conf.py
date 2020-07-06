from os import environ

from flask_env import MetaFlaskEnv
from libtrustbridge.utils.conf import env_s3_config, env_queue_config

from api.aws import string_or_b64kms


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SERVICE_NAME = 'shared-db-channel'
    SERVER_NAME = 'localhost:5000'
    ENDPOINT = 'AU'
    LOG_FORMATTER_JSON = False
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SENTRY_DSN = environ.get("SENTRY_DSN")

    def __init__(self):
        if not hasattr(self, 'SUBSCRIPTIONS_REPO_CONF'):
            self.SUBSCRIPTIONS_REPO_CONF = env_s3_config('SUBSCRIPTIONS_REPO')
        if not hasattr(self, 'NOTIFICATIONS_REPO_CONF'):
            self.NOTIFICATIONS_REPO_CONF = env_queue_config('NOTIFICATIONS_REPO')
        if not hasattr(self, 'DELIVERY_OUTBOX_REPO_CONF'):
            self.DELIVERY_OUTBOX_REPO_CONF = env_queue_config('DELIVERY_OUTBOX_REPO')
        if not hasattr(self, 'CHANNEL_REPO_CONF'):
            self.CHANNEL_REPO_CONF = env_s3_config('CHANNEL_REPO')


class ProductionConfig(BaseConfig):
    ENV = 'production'


class AWSProductionConfig(ProductionConfig):
    """Support for sensitive env vars encrypted with AWS KMS"""
    KMS_PREFIX = environ.get('KMS_PREFIX', None)
    AWS_REGION = environ.get('AWS_REGION', None)
    if KMS_PREFIX and AWS_REGION:
        SQLALCHEMY_DATABASE_URI = string_or_b64kms(environ.get('DATABASE_URI'), KMS_PREFIX, AWS_REGION)


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    LOCAL_DB = 'postgresql+psycopg2://dbchannel:dbchannel@127.0.0.1/dbchannel'
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URI', LOCAL_DB)


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ENDPOINT = 'AU'
    SERVER_NAME = 'localhost'
    test_minio = {
        'use_ssl': False,
        'host': environ.get('TEST_MINIO_HOST'),
        'port': environ.get('TEST_MINIO_PORT'),
        'bucket': 'default',
        'region': 'test_region',
        'access_key': environ.get('TEST_MINIO_ACCESS_KEY'),
        'secret_key': environ.get('TEST_MINIO_SECRET_KEY')
    }
    SUBSCRIPTIONS_REPO_CONF = test_minio
    CHANNEL_REPO_CONF = test_minio

    test_elastic = {
            'use_ssl': False,
            'host': environ.get('TEST_ELASTICMQ_REPO_HOST'),
            'port': environ.get('TEST_ELASTICMQ_REPO_PORT'),
            'context-path': '',
            'region': 'elasticmq',
            'access_key': 'x',
            'secret_key': 'x'
    }

    NOTIFICATIONS_REPO_CONF = test_elastic.copy()
    NOTIFICATIONS_REPO_CONF['queue_name'] = 'test-notifications'

    DELIVERY_OUTBOX_REPO_CONF = test_elastic.copy()
    DELIVERY_OUTBOX_REPO_CONF['queue_name'] = 'test-delivery-outbox'
