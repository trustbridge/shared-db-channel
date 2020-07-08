#!/usr/bin/env python
"""Provides management tasks which can be used for production deployments.
includes manage commands for docker and lambda handlers"""

import os
from flask_migrate import Migrate, MigrateCommand, upgrade
from flask_script import Server, Manager

from api.app import create_app, db
from api import commands
from api.conf import ProductionConfig

app = create_app(config_object=ProductionConfig())
manager = Manager(app)

manager.add_command('run_callback_spreader', commands.RunCallbackSpreaderProcessorCommand)
manager.add_command('run_callback_delivery', commands.RunCallbackDeliveryProcessorCommand)
manager.add_command('run_message_observer', commands.RunNewMessagesObserverCommand)

if __name__ == "__main__":
    manager.run()


"""lambda handler entry points"""
def dbupgrade_handler(event, context):
    revision = os.getenv('DB_REVISION', 'head')
    with app.app_context():
        upgrade(revision=revision)
