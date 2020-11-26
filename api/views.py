import json
import uuid
from http import HTTPStatus

import marshmallow
import requests
from flask import Blueprint, Response, request, jsonify
from flask import current_app
from flask.views import View
from libtrustbridge.utils.routing import mimetype
from libtrustbridge.websub.constants import MODE_ATTR_SUBSCRIBE_VALUE
from libtrustbridge.websub.exceptions import SubscriptionNotFoundError
from libtrustbridge.websub.repos import SubscriptionsRepo, NotificationsRepo
from libtrustbridge.websub.schemas import SubscriptionForm
from webargs import fields
from webargs.flaskparser import use_kwargs
from werkzeug.exceptions import HTTPException

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
    # mostly for Sentry debug - this page is not loaded frequently anyway
    current_app.logger.warning("Index page is loaded")
    return JsonResponse(data)


@blueprint.route('/messages', methods=['POST'])
def post_message():
    """
    ---
    post:
        servers:
            - url: https://sharedchannel-c1.services.devnet.trustbridge.io/
        description:
            Post a new message endpoint
        requestBody:
            content:
                application/json:
                    schema: MessagePayloadSchema
                    example:
                        sender: AU
                        receiver: CN
                        subject: AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX
                        obj: QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n
                        predicate: UN.CEFACT.Trade.CertificateOfOrigin.created
        responses:
            201:
                description: Returns message id
                content:
                    application/json:
                        schema: PostedMessageSchema
                        example:
                            id: 1
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
    use_case = use_cases.PublishStatusChangeUseCase(notifications_repo)
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
    ---
    get:
        servers:
            - url: https://sharedchannel-c1.services.devnet.trustbridge.io/
        description:
            Get message by ID
        parameters:
            - name: id
              in: path
              required: true
              schema:
                type: integer
                format: int64
              example: 123
            - in: query
              name: fields
              schema:
                type: array
                items:
                  type: string
              style: form
              explode: false
              example: id,status,message
        responses:
            200:
                description: Returns message object
                content:
                    application/json:
                        schema: MessageSchema
                        example:
                            id: 123
                            message:
                                sender: AU
                                receiver: CN
                                subject: AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX
                                obj: QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n
                                predicate: UN.CEFACT.Trade.CertificateOfOrigin.created
                            status: received
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

        current_app.logger.info("Subscription request received: %s", form_data)

        topic = self.get_topic(form_data)
        callback = form_data['callback']
        mode = form_data['mode']
        lease_seconds = form_data['lease_seconds']
        try:
            self.verify(callback, mode, topic, lease_seconds)
        except IntentVerificationFailure:
            current_app.logger.error(
                "Intent verification failed for the %s", form_data.get("callback")
            )
            return JsonResponse({'error': 'Intent verification failed'}, status=HTTPStatus.BAD_REQUEST)

        if mode == MODE_ATTR_SUBSCRIBE_VALUE:
            current_app.logger.info(
                "Subscribed %s to %s", form_data.get("callback"), form_data.get("topic")
            )
            self._subscribe(callback, topic, lease_seconds)
        else:
            current_app.logger.info(
                "Unsubscribed %s from %s", form_data.get("callback"), form_data.get("topic")
            )
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
    """
    ---
    post:
        servers:
            - url: https://sharedchannel-c1.services.devnet.trustbridge.io/
        description:
            Subscribe to updates about a message (ie. status updates)
        requestBody:
            content:
                application/x-www-form-urlencoded:
                    schema: SubscriptionForm
                    example:
                        hub.mode: subscribe
                        hub.topic: 123
                        hub.callback: 'https://callback.url/1'
        responses:
            202:
                description: Client successfully subscribed/unsubscribed
            400:
                description: Wrong params or intent verification failure
    """


class SubscriptionByJurisdiction(BaseSubscriptionsView):
    """
    ---
    post:
        servers:
            - url: https://sharedchannel-c1.services.devnet.trustbridge.io/
        description:
            Subscribe to updates about new messages sent to jurisdiction (AU, SG, etc.)
        requestBody:
            content:
                application/x-www-form-urlencoded:
                    schema: SubscriptionForm
                    example:
                        hub.mode: subscribe
                        hub.topic: 'AU'
                        hub.callback: 'https://callback.url/1'
        responses:
            202:
                description: Client successfully subscribed/unsubscribed
            400:
                description: Wrong params or intent verification failure
    """
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


@blueprint.app_errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@blueprint.app_errorhandler(Exception)
def handle_unexpected_error(error):
    current_app.logger.exception(error)
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': 'UnexpectedException',
            'message': 'An unexpected error has occurred.',
            'details': str(error),
        }
    }

    return jsonify(response), status_code
