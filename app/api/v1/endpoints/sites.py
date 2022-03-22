from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import SITES
from app.db.session import get_db
from app.schemas import CaseSchemaCreate, CaseSchemaWithTaskInfo, SiteSchema

from .cases import create_case

router = APIRouter()


@router.get("/", response_model=List[SiteSchema])
def get_sites() -> Any:
    """
    Get all sites
    """
    return SITES


@router.post("/{site_name}", response_model=CaseSchemaWithTaskInfo)
def create_site_case(site_name: str, db: Session = Depends(get_db)) -> Any:
    """
    Create a site
    """
    site = next(filter(lambda s: s.name == site_name, SITES), None)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    data = CaseSchemaCreate(
        name=site_name, compset=site.compset, res=site.res, data_url=site.url
    )
    case = create_case(db=db, data=data)
    return case
