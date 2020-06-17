import pytest
import responses
from freezegun import freeze_time
from libtrustbridge.websub.repos import SubscriptionsRepo, NotificationsRepo

from api.app import create_app, db
from api.conf import TestingConfig
from api.models import Message
from api.repos import ChannelRepo


@pytest.fixture(scope='session')
def app():
    yield create_app(TestingConfig())


@pytest.fixture(scope='session')
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


@pytest.fixture
def clean_subscriptions_repo(app, request):
    repo = SubscriptionsRepo(app.config['SUBSCRIPTIONS_REPO_CONF'])
    repo._unsafe_method__clear()
    if request.cls is not None:
        request.cls.subscriptions_repo = repo
    yield repo
    repo._unsafe_method__clear()


@pytest.fixture
def clean_notifications_repo(app, request):
    repo = NotificationsRepo(app.config['NOTIFICATIONS_REPO_CONF'])
    repo._unsafe_method__clear()
    if request.cls is not None:
        request.cls.notifications_repo = repo
    yield repo
    repo._unsafe_method__clear()


@pytest.fixture
def clean_channel_repo(app, request):
    repo = ChannelRepo(app.config['CHANNEL_REPO_CONF'])
    repo._unsafe_method__clear()
    if request.cls is not None:
        request.cls.channel_repo = repo
    yield repo
    repo._unsafe_method__clear()


@pytest.fixture
def mocked_responses(request):
    with responses.RequestsMock() as rsps:
        if request.cls is not None:
            request.cls.mocked_responses = rsps
        yield rsps
