from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

spec = APISpec(
    title="Shared DB Channel API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin()
    ],
)
