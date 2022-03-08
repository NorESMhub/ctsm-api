from fastapi import APIRouter

from app.api.api_v1.endpoints import cases

# Add all the API endpoints from the endpoints folder
api_router = APIRouter()
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
