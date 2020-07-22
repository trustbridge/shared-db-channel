from urllib.parse import urljoin

from flask import Flask, url_for
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from libtrustbridge.errors import handlers

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

    SENTRY_DSN = app.config.get("SENTRY_DSN")
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(SENTRY_DSN, integrations=[FlaskIntegration()])

    db.init_app(app)

    with app.app_context():
        from api import views

        app.register_blueprint(views.blueprint)

        ma.init_app(app)
        migrate.init_app(app, db)

        handlers.register(app)
        register_specs(app)

        app.config['HUB_URL'] = f"{app.config['SERVICE_URL']}/messages/subscriptions/by_id"
        # app.config['HUB_URL'] = urljoin(
        #     app.config['SERVICE_URL'],
        #     url_for('views.subscriptions_by_id', _external=False)
        # )
    return app


def register_specs(app):
    for view in app.view_functions.values():
        views = ('post_message', 'get_message', 'subscriptions_by_jurisdiction', 'subscriptions_by_id')
        if view.__name__ in views:
            spec.path(view=view, app=app)
