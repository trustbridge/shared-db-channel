from api.app import create_app
from api.conf import AWSProductionConfig

app = create_app(AWSProductionConfig())
