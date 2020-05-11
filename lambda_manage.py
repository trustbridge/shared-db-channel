import os
import logging

from flask_migrate import upgrade, current

from api.app import create_app, db
from api.conf import AWSProductionConfig

logger = logging.getLogger(__name__)
app = create_app(AWSProductionConfig())

def dbmgmt_handler(event, context):

    revision = os.getenv('DB_REVISION', 'head')
    task = 'upgrade'

    if event.get('task'):
        task = event.get('task')

    if task == 'upgrade':
        with app.app_context():
            upgrade(revision=revision)

    elif task == 'current':
        with app.app_context():
            current()

    return {
        'task' : task
    }

if __name__ == "__main__":
    dbmgmt_handler({},{})
