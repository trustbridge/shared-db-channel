import logging

from api.app import create_app
from api.conf import ProductionConfig

logger = logging.getLogger(__name__)

app = create_app(ProductionConfig())
