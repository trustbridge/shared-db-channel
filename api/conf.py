from os import environ

from flask_env import MetaFlaskEnv
from libtrustbridge.utils.conf import env_s3_config

from api.aws import string_or_b64kms


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SERVICE_NAME = 'shared-db-channel'
    LOG_FORMATTER_JSON = False
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self):
        if not hasattr(self, 'SUBSCRIPTION_REPO_CONF'):
            self.SUBSCRIPTION_REPO_CONF = env_s3_config('SUBSCR_API_REPO')


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
    SERVER_NAME = 'localhost'
    SUBSCRIPTION_REPO_CONF = {
        'use_ssl': False,
        'host': environ.get('TEST_SUBSCRIPTION_REPO_HOST'),
        'port': '9000',
        'bucket': 'default',
        'region': 'test_region',
        'secret_key': 'minio_secret_key',
        'access_key': 'minio_access_key'
    }
