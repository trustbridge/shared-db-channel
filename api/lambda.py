from api.app import create_app
from api.conf import ProductionConfig

app = create_app(ProductionConfig())
