import json
import uuid
from http import HTTPStatus

import marshmallow
import requests
from flask import Blueprint, Response, request
from flask import current_app
from flask.views import View
from libtrustbridge.utils.routing import mimetype
from libtrustbridge.websub.constants import MODE_ATTR_SUBSCRIBE_VALUE
from libtrustbridge.websub.exceptions import SubscriptionNotFoundError
from libtrustbridge.websub.repos import SubscriptionsRepo, NotificationsRepo
from libtrustbridge.websub.schemas import SubscriptionForm
from webargs import fields
from webargs.flaskparser import use_kwargs

from api import use_cases
from api.models import Message, db
from api.schemas import MessagePayloadSchema, PostedMessageSchema, MessageSchema, StatusUpdateSchema, dump_only_fields

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

    notifications_repo = NotificationsRepo(current_app.config['NOTIFICATIONS_REPO_CONF'])
    use_case = use_cases.PublishNewMessageUseCase(notifications_repo)
    use_case.publish(message)

    hub_url = current_app.config['HUB_URL']
    topic = use_cases.PublishStatusChangeUseCase.get_topic(message)
    headers = {
        'Link': f'<{hub_url}>; rel="hub", <{topic}>; rel="self"'
    }
    return JsonResponse(return_schema.dump(message), status=201, headers=headers)


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


@blueprint.route('/messages/<id>/status', methods=['PUT'])
def update_message_status(id):
    """Update message status"""
    message = db.session.query(Message).get(id)
    if not message:
        return Response(status=404)

    data = request.form.to_dict()
    schema = StatusUpdateSchema()
    try:
        schema.load(data, instance=message, partial=True)
    except marshmallow.ValidationError as e:
        return JsonResponse(e.messages, status=400)

    notifications_repo = NotificationsRepo(current_app.config['NOTIFICATIONS_REPO_CONF'])
    use_case = use_cases.PublishStatusChangeUseCase(notifications_repo)
    use_case.publish(message)

    db.session.commit()
    return JsonResponse(MessageSchema().dump(message))


class IntentVerificationFailure(Exception):
    pass


class BaseSubscriptionsView(View):
    methods = ['POST']

    @mimetype(include=['application/x-www-form-urlencoded'])
    def dispatch_request(self):
        try:
            form_data = SubscriptionForm().load(request.form.to_dict())
        except marshmallow.ValidationError as e:  # TODO integrate marshmallow and libtrustbridge.errors.handlers
            return JsonResponse(e.messages, status=HTTPStatus.BAD_REQUEST)

        topic = self.get_topic(form_data)
        callback = form_data['callback']
        mode = form_data['mode']
        lease_seconds = form_data['lease_seconds']

        try:
            self.verify(callback, mode, topic, lease_seconds)
        except IntentVerificationFailure:
            return JsonResponse({'error': 'Intent verification failed'}, status=HTTPStatus.BAD_REQUEST)

        if mode == MODE_ATTR_SUBSCRIBE_VALUE:
            self._subscribe(callback, topic, lease_seconds)
        else:
            self._unsubscribe(callback, topic)

        return JsonResponse(status=HTTPStatus.ACCEPTED)

    def get_topic(self, form_data):
        return form_data['topic']

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

    def verify(self, callback_url, mode, topic, lease_seconds):
        challenge = str(uuid.uuid4())
        params = {
            'hub.mode': mode,
            'hub.topic': topic,
            'hub.challenge': challenge,
            'hub.lease_seconds': lease_seconds
        }
        response = requests.get(callback_url, params)
        if response.status_code == 200 and response.text == challenge:
            return

        raise IntentVerificationFailure()


class SubscriptionById(BaseSubscriptionsView):
    pass


class SubscriptionByJurisdiction(BaseSubscriptionsView):
    def get_topic(self, form_data):
        return "jurisdiction.%s" % form_data['topic']


blueprint.add_url_rule(
    '/messages/subscriptions/by_jurisdiction',
    view_func=SubscriptionByJurisdiction.as_view('subscriptions_by_jurisdiction')
)
blueprint.add_url_rule(
    '/messages/subscriptions/by_id',
    view_func=SubscriptionById.as_view('subscriptions_by_id')
)
