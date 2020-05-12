import os
import logging

from flask_migrate import upgrade

from api.app import create_app
from api.conf import AWSProductionConfig

logger = logging.getLogger(__name__)
app = create_app(AWSProductionConfig())

def dbupgrade_handler(event, context):

    revision = os.getenv('DB_REVISION', 'head')
    with app.app_context():
        upgrade(revision=revision)
