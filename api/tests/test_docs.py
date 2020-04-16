from apispec.utils import validate_spec

from api.docs import spec


def test_post_message__should_be_registered_in_docs(app):
    with open('swagger.yaml') as fp:
        assert spec.to_yaml() == fp.read()


def test_spec__should_be_valid():
    assert validate_spec(spec)
