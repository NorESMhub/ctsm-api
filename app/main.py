from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core import settings
from app.utils.dependencies import check_dependencies
from app.utils.logger import logger

try:
    check_dependencies()
except Exception as e:
    logger.error(e)
    exit(1)

app = FastAPI(
    title="CTSM API",
    openapi_url=f"{settings.API_V1}/openapi.json",
    docs_url=f"{settings.API_V1}/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1)
