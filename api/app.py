from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from api import loggers
from api.conf import BaseConfig

db = SQLAlchemy()
ma = Marshmallow()


def create_app(config_object=None):
    """
    FLASK_ENV=development flask run --port=5001
    """

    if config_object is None:
        config_object = BaseConfig

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.logger = loggers.create_logger(app.config)

    from api import views
    app.register_blueprint(views.blueprint)

    db.init_app(app)
    ma.init_app(app)

    return app
