from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db.session import get_db
from app.utils.sites import get_all_sites, get_site_by_name

from .cases import create_case

router = APIRouter()


@router.get("/", response_model=List[schemas.Site])
def get_sites() -> Any:
    """
    Get all sites.
    """
    return get_all_sites()


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


@router.post("/{site_name}", response_model=schemas.CaseWithTaskInfo)
def create_site_case(
    site_name: str,
    variables: Dict[str, Any],
    driver: schemas.CTSMDriver = schemas.CTSMDriver.mct,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a case for the given site.
    """
    site = get_site_by_name(site_name)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    data = schemas.CaseBase(
        compset=site.compset,
        res=site.res,
        variables=variables,
        data_url=site.url,
        driver=driver,
    )
    case_task = create_case(data=data, db=db)
    obj_in = schemas.SiteCaseDBCreate(
        name=site_name,
        case_id=case_task.case.id,
    )
    site_cases = crud.site.get_site_cases(db=db, site_name=site_name)
    site_case = next((c for c in site_cases if c.case.id == case_task.case.id), None)
    if not site_case:
        crud.site.create(db=db, obj_in=obj_in)
    return case_task
