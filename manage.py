#!/usr/bin/env python
from flask_migrate import Migrate, MigrateCommand
from flask_script import Server, Manager

from api.app import create_app, db

app = create_app(config_object='api.conf.DevelopmentConfig')
manager = Manager(app)

migrate = Migrate(app, db)

manager.add_command("runserver", Server())
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()
