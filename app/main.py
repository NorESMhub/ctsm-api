from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import API_V1, get_settings
from app.utils.dependencies import check_dependencies
from app.utils.logger import logger

try:
    check_dependencies()
except Exception as e:
    logger.error(e)
    exit(1)

settings = get_settings()

app = FastAPI(
    title="CTSM API",
    openapi_url=f"{API_V1}/openapi.json",
    docs_url=f"{API_V1}/docs",
    redoc_url=None,
)

app.include_router(api_router, prefix=API_V1)
