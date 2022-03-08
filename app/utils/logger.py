import logging

from app.core.config import get_settings

settings = get_settings()

FORMAT = "[%(levelname)s] %(asctime)s %(message)s"
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO, format=FORMAT
)
logger = logging.getLogger("CTSM API")
