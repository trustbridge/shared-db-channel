from collections import OrderedDict

from api.docs import spec


def test_post_message__should_be_registered_in_docs(app):
    with app.app_context():
        assert spec.to_dict() == {
            'info': {'title': 'Shared DB Channel API', 'version': '1.0.0'},
            'openapi': '3.0.2',
            'components': {
                'schemas': {
                    'Message': {
                        'properties': {
                            'id': {
                                'format': 'int32',
                                'readOnly': True,
                                'type': 'integer'
                            },
                            'obj': {'type': 'string'},
                            'predicate': {'type': 'string'},
                            'receiver': {'type': 'string'},
                            'sender': {'type': 'string'},
                            'subject': {'type': 'string'}
                        },
                        'required': [
                            'obj',
                            'predicate',
                            'receiver',
                            'sender',
                            'subject'
                        ],
                        'type': 'object'
                    }
                }
            },
            'paths': OrderedDict([
                ('/messages', OrderedDict([
                    ('post', {
                        'requestBody': {
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/Message'}
                                }
                            }
                        },
                        'responses': OrderedDict([
                            ('201', {
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/Message'}
                                    }
                                },
                            })
                        ])
                    })
                ]))
            ])
        }
