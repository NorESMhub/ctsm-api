from fastapi import APIRouter

from app.api.v1.endpoints import cases, sites, tasks

# Add all the API endpoints from the endpoints folder
api_router = APIRouter()
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(sites.router, prefix="/sites", tags=["sites"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
