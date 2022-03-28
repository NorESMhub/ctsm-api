import logging

from app.core import settings

FORMAT = "[%(levelname)s] %(asctime)s %(message)s"
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO, format=FORMAT
)
logger = logging.getLogger("CTSM API")
