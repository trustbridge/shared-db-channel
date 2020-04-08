import pytest

from api.app import create_app, db
from api.conf import TestingConfig


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
