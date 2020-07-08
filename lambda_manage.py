"""Provides management tasks which can be invoked using AWS Lambda.
Each task you want to complete is configured with a lambda handler."""
import os

from flask_migrate import upgrade

from api.app import create_app
from api.conf import ProductionConfig


app = create_app(ProductionConfig())


def dbupgrade_handler(event, context):
    revision = os.getenv('DB_REVISION', 'head')
    with app.app_context():
        upgrade(revision=revision)
