from apispec.utils import validate_spec

from api.docs import spec


def test_generated_swagger_file_is_up_to_date(app):
    with open('swagger.yaml') as fp:
        assert spec.to_yaml() == fp.read()


def test_spec__should_be_valid():
    assert validate_spec(spec)
