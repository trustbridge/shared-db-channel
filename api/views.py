import json
import marshmallow
from http import HTTPStatus

from flask import Blueprint, Response, request
from flask import current_app
from flask.views import View

from webargs import fields
from webargs.flaskparser import use_kwargs

from libtrustbridge.utils.routing import mimetype
from libtrustbridge.websub.constants import MODE_ATTR_SUBSCRIBE_VALUE
from libtrustbridge.websub.exceptions import SubscriptionNotFoundError
from libtrustbridge.websub.repos import SubscriptionsRepo
from libtrustbridge.websub.schemas import SubscriptionForm

from api.models import Message, db
from api.schemas import MessagePayloadSchema, PostedMessageSchema, MessageSchema, dump_only_fields
from api import use_cases

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
    except marshmallow.ValidationError as e:
        return JsonResponse(e.messages, status=400)

    message = Message(payload=request.json)
    db.session.add(message)
    db.session.commit()
    return_schema = PostedMessageSchema()
    return JsonResponse(return_schema.dump(message), status=201)


@blueprint.route('/messages/<id>')
@use_kwargs({'fields': fields.DelimitedList(fields.Str())}, location="querystring")
def get_message(id, fields=None):
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
            - in: query
              name: fields
              schema:
                type: array
                items:
                  type: string
              style: form
              explode: false
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

    data = return_schema.dump(message)
    return JsonResponse(dump_only_fields(data, fields))


class SubscriptionsView(View):
    methods = ['POST']

    @mimetype(include=['application/x-www-form-urlencoded'])
    def dispatch_request(self):
        try:
            form_data = SubscriptionForm().load(request.form.to_dict())
        except marshmallow.ValidationError as e:  # TODO integrate marshmallow and libtrustbridge.errors.handlers
            return JsonResponse(e.messages, status=400)

        if form_data['mode'] == MODE_ATTR_SUBSCRIBE_VALUE:
            self._subscribe(form_data['callback'], form_data['topic'], form_data['lease_seconds'])
        else:
            self._unsubscribe(form_data['callback'], form_data['topic'])

        return Response(status=HTTPStatus.ACCEPTED)

    def _subscribe(self, callback, topic, lease_seconds):
        repo = self._get_repo()
        use_case = use_cases.SubscriptionRegisterUseCase(repo)
        use_case.execute(callback, topic, lease_seconds)

    def _unsubscribe(self, callback, topic):
        repo = self._get_repo()
        use_case = use_cases.SubscriptionDeregisterUseCase(repo)
        try:
            use_case.execute(callback, topic)
        except use_cases.SubscriptionNotFound as e:
            raise SubscriptionNotFoundError() from e

    def _get_repo(self):
        return SubscriptionsRepo(current_app.config.get('SUBSCRIPTIONS_REPO_CONF'))


blueprint.add_url_rule('/subscriptions/', view_func=SubscriptionsView.as_view('subscriptions'))
