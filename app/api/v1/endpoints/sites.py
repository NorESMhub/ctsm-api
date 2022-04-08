from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import parse_file_as
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import settings
from app.db.session import get_db

router = APIRouter()


def get_all_sites() -> schemas.FeatureCollection[schemas.SiteProperties]:
    return (
        parse_file_as(
            schemas.FeatureCollection[schemas.SiteProperties], settings.SITES_PATH
        )
        if settings.SITES_PATH.exists()
        else schemas.FeatureCollection[schemas.SiteProperties](features=[])
    )


def get_site_by_name(site_name: str) -> Optional[schemas.SiteProperties]:
    """
    Return the site info for a given site name from `resources/config/sites.json`.
    """
    sites = get_all_sites()
    features = sites.features if sites else []
    site = next(
        filter(lambda f: f.properties and f.properties.name == site_name, features),
        None,
    )

    if site:
        return site.properties

    return None


@router.get("/", response_model=schemas.FeatureCollection[schemas.SiteProperties])
def get_sites() -> Any:
    """
    Get all sites.
    """
    return get_all_sites()


@router.post("/", response_model=schemas.CaseWithTaskInfo)
def create_site_case(
    site_case: schemas.SiteCaseCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a case for the given site.

    Clients need to include variable name and value. Other fields will be ignored and the actual configured properties
    will be used.
    - See CaseVariableConfig schema for all the possible fields.
    - See /cases/variables endpoint for a full list of allowed variables and their properties.
    """
    site = get_site_by_name(site_case.site_name)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    data = schemas.CaseBase(
        compset=site.compset,
        res=site.res,
        variables=site_case.variables,
        data_url=site.url,
        driver=site_case.driver,
    )
    case = crud.case.create(db, obj_in=data)
    case_task = schemas.CaseWithTaskInfo.get_case_with_task_info(case)
    assert case_task  # This should never fail
    obj_in = schemas.SiteCaseDBCreate(
        name=site_case.site_name,
        case_id=case_task.id,
    )
    site_cases = crud.site.get_site_cases(db=db, site_name=site_case.site_name)
    existing_site_case = next((c for c in site_cases if c.id == case_task.id), None)
    if not existing_site_case:
        crud.site.create(db=db, obj_in=obj_in)
    return case_task


@router.get("/{site_name}/cases", response_model=List[schemas.CaseWithTaskInfo])
def get_site_cases(
    site_name: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all the cases for a site and given drivers.
    By default, all drivers are returned.
    """
    return crud.site.get_site_cases(db=db, site_name=site_name)
