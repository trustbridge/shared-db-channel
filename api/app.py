from flask import Flask
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from api import loggers
from api.conf import BaseConfig
from api.docs import spec

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()


def create_app(config_object=None):
    if config_object is None:
        config_object = BaseConfig

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.logger = loggers.create_logger(app.config)

    db.init_app(app)

    with app.app_context():

        from api import views

        app.register_blueprint(views.blueprint)

        ma.init_app(app)
        migrate.init_app(app, db)

        register_specs(app)
    return app


def register_specs(app):
    for view in app.view_functions.values():
        if view.__name__ in ('post_message', 'get_message'):
            spec.path(view=view, app=app)
