from marshmallow import fields

from api import models
from api.app import ma


class MessagePayloadSchema(ma.Schema):
    sender = fields.String(required=True)
    receiver = fields.String(required=True)
    subject = fields.String(required=True)
    obj = fields.String(required=True)
    predicate = fields.String(required=True)


class PostedMessageSchema(ma.SQLAlchemySchema):
    id = fields.Integer(dump_only=True)

    class Meta:
        model = models.Message
