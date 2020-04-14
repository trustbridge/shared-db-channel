from os import environ

from flask_env import MetaFlaskEnv


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SERVICE_NAME = 'shared-rds-channel'
    LOG_FORMATTER_JSON = False
    SQLALCHEMY_DATABASE_URI = environ.get('RDS_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(BaseConfig):
    ENV = 'production'


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    LOCAL_DB = 'postgresql+psycopg2://rdschannel:rdschannel@127.0.0.1/rdschannel'
    SQLALCHEMY_DATABASE_URI = environ.get('RDS_DATABASE_URI', LOCAL_DB)


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SERVER_NAME = 'localhost'
