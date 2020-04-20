import pytest
from freezegun import freeze_time

from api.app import create_app, db
from api.conf import TestingConfig
from api.models import Message


@pytest.yield_fixture(scope='session')
def app():
    yield create_app(TestingConfig)


@pytest.yield_fixture(scope='session')
def _db(app):
    db.app = app
    db.create_all()
    yield db
    db.drop_all()


@pytest.yield_fixture(scope='session')
def client(app):
    with app.app_context():
        yield app.test_client()


@pytest.fixture
@freeze_time('2020-04-07 14:21:22.123456')
def message(db_session):
    message = Message(id=42, payload={"sender": "AU"})
    db_session.add(message)
    db_session.commit()
    return message
