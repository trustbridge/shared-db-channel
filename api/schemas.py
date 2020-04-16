from marshmallow import fields

from api import models
from api.app import ma


class MessageSchema(ma.SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    sender = fields.String(required=True)
    receiver = fields.String(required=True)
    subject = fields.String(required=True)
    obj = fields.String(required=True)
    predicate = fields.String(required=True)

    class Meta:
        model = models.Message


class PostedMessageSchema(ma.SQLAlchemySchema):
    id = fields.Integer(dump_only=True)

    class Meta:
        model = models.Message
