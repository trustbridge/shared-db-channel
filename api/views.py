import json

from flask import Blueprint, Response, request
from flask import current_app
from marshmallow import ValidationError

from api.models import Message, db
from api.schemas import MessagePayloadSchema, PostedMessageSchema, MessageSchema

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
                    schema: MessagePayloadSchema
        responses:
            201:
                description: Returns message id
                content:
                    application/json:
                        schema: PostedMessageSchema
    """
    schema = MessagePayloadSchema()
    try:
        schema.load(request.json)
    except ValidationError as e:
        return JsonResponse(e.messages, status=400)

    message = Message(payload=request.json)
    db.session.add(message)
    db.session.commit()
    return_schema = PostedMessageSchema()
    return JsonResponse(return_schema.dump(message), status=201)


@blueprint.route('/messages/<id>')
def get_message(id):
    """
    Get message by ID
    ---
    get:
        parameters:
            - name: id
              in: path
              required: true
              schema:
                type: integer
                format: int64
        responses:
            200:
                description: Returns message object
                content:
                    application/json:
                        schema: MessageSchema
    """
    message = db.session.query(Message).get(id)
    if not message:
        return Response(status=404)
    return_schema = MessageSchema()
    return JsonResponse(return_schema.dump(message))
