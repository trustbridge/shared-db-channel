import pytest
from freezegun import freeze_time
from libtrustbridge.websub.repos import SubscriptionsRepo

from api.app import create_app, db
from api.conf import TestingConfig
from api.models import Message


@pytest.yield_fixture(scope='session')
def app():
    yield create_app(TestingConfig())


@pytest.yield_fixture(scope='session')
def _db(app):
    db.app = app
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
@freeze_time('2020-04-07 14:21:22.123456')
def message(db_session):
    message = Message(id=42, payload={"sender": "AU"})
    db_session.add(message)
    db_session.commit()
    return message


@pytest.yield_fixture()
def clean_subscriptions_repo(app, request):
    repo = SubscriptionsRepo(app.config['SUBSCRIPTIONS_REPO_CONF'])
    assert repo._unsafe_is_empty_for_test()
    if request.cls is not None:
        request.cls.subscriptions_repo = repo
    yield repo
    repo._unsafe_clear_for_test()
