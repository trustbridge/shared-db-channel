import pytest
from marshmallow import ValidationError

from api import schemas


class TestMessageSchema:
    TEST_MESSAGE = {
        'obj': 'QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n',
        'predicate': 'UN.CEFACT.Trade.CertificateOfOrigin.created',
        'receiver': 'CN',
        'sender': 'AU',
        'subject': 'AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX'
    }

    def test_load__when_all_fields_given(self):
        schema = schemas.MessagePayloadSchema()

        message_model = schema.load(self.TEST_MESSAGE)
        assert message_model == self.TEST_MESSAGE

    def test_load__when_missing_field__should_raise_error(self):
        schema = schemas.MessagePayloadSchema()
        with pytest.raises(ValidationError) as excinfo:
            schema.load({})

        assert excinfo.value.messages == {
            'obj': ['Missing data for required field.'],
            'sender': ['Missing data for required field.'],
            'receiver': ['Missing data for required field.'],
            'predicate': ['Missing data for required field.'],
            'subject': ['Missing data for required field.']
        }
