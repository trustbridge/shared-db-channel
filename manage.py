#!/usr/bin/env python
from flask_script import Server, Manager

from api.app import create_app

app = create_app(config_object='api.conf.DevelopmentConfig')
manager = Manager(app)


manager.add_command("runserver", Server())

if __name__ == "__main__":
    manager.run()
