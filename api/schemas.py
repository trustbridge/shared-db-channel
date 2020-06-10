from marshmallow import fields, post_load
from marshmallow_enum import EnumField

from api import models
from api.app import ma


def dump_only_fields(data: dict, fields: list):
    """
    If fields provided, returns dict filtered by keys that in field list.
    """
    if not fields:
        return data
    return {k: v for k, v in data.items() if k in fields}


class MessagePayloadSchema(ma.Schema):
    sender = fields.String(required=True)
    receiver = fields.String(required=True)
    subject = fields.String(required=True)
    obj = fields.String(required=True)
    predicate = fields.String(required=True)


class MessageSchema(ma.SQLAlchemyAutoSchema):
    status = fields.String(attribute='status.value')
    message = fields.Dict(attribute='payload')

    class Meta:
        model = models.Message
        fields = ('id', 'status', 'message')


class PostedMessageSchema(ma.SQLAlchemySchema):
    id = fields.Integer(dump_only=True)

    class Meta:
        model = models.Message


class StatusUpdateSchema(ma.SQLAlchemySchema):
    status = EnumField(models.MessageStatus, by_value=True)

    class Meta:
        model = models.Message

    @post_load
    def make_message(self, data, **kwargs):
        self.instance.status = data['status']
        return self.instance
