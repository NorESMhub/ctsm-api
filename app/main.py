from typing import Awaitable, Callable

import pydantic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

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

allowed_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


async def catch_exceptions_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Using this middleware we can return exceptions to the client as needed, while letting CORS middleware being applied.
    Otherwise, errors won't be returned for requests from clients with different origins.
    """
    origin = request.headers.get("Origin")
    error_headers = (
        {"Access-Control-Allow-Origin": origin}
        if origin and origin in allowed_origins
        else {}
    )

    try:
        return await call_next(request)
    except pydantic.ValidationError as exc:
        logger.exception(exc)
        return Response(exc.json(), status_code=500, headers=error_headers)
    except Exception as exc:
        logger.exception(exc)
        return Response("Internal server error", status_code=500, headers=error_headers)


app.middleware("http")(catch_exceptions_middleware)

app.include_router(api_router, prefix=settings.API_V1)
