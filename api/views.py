import json

from flask import Blueprint, Response, request
from flask import current_app
from marshmallow import ValidationError

from api.models import Message, db
from api.schemas import MessageSchema

blueprint = Blueprint('views', __name__)


class JsonResponse(Response):
    default_mimetype = 'application/json'

    def __init__(self, response=None, *args, **kwargs):
        if response:
            response = json.dumps(response)

        super().__init__(response, *args, **kwargs)


@blueprint.route('/', methods=['GET'])
def index():
    data = {
        "service": current_app.config.get('SERVICE_NAME'),
    }
    return JsonResponse(data)


@blueprint.route('/messages', methods=['POST'])
def post_message():
    """
    Post a new message endpoint
    ---
    post:
        requestBody:
            content:
                application/json:
                    schema: MessageSchema
        responses:
            201:
                description: Returns created message object
                content:
                    application/json:
                        schema: MessageSchema
    """
    schema = MessageSchema()
    try:
        message_dict = schema.load(request.json)
    except ValidationError as e:
        return JsonResponse(e.messages, status=400)
    db.session.add(Message(**message_dict))
    db.session.commit()

    return JsonResponse(message_dict, status=201)
