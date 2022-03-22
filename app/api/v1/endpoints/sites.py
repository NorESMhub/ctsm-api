from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import SITES
from app.crud import crud_case
from app.db.session import get_db
from app.schemas import (
    CaseSchema,
    CaseSchemaCreate,
    CaseSchemaWithTaskInfo,
    CTSMDriver,
    SiteSchema,
)
from app.tasks import celery_app
from app.utils.sites import get_site_by_name, get_site_id

from .cases import create_case

router = APIRouter()


@router.get("/", response_model=List[SiteSchema])
def get_sites() -> Any:
    """
    Get all sites.
    """
    return SITES


@router.get("/{site_name}/cases", response_model=List[CaseSchemaWithTaskInfo])
def get_site_cases(
    site_name: str,
    drivers: Optional[List[CTSMDriver]] = Query([]),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all the cases for a site and given drivers.
    By default, all drivers are returned.
    """
    site = get_site_by_name(site_name)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    cases = []
    for driver in drivers or CTSMDriver:
        case_id = get_site_id(site.compset, site.res, driver, site.url)
        case = crud_case.get(db, id=case_id)
        if case:
            task = celery_app.AsyncResult(case.task_id)
            error = task.traceback.strip().split("\n")[-1] if task.traceback else None
            cases.append(
                CaseSchemaWithTaskInfo(
                    case=CaseSchema.from_orm(case),
                    task_id=task.id,
                    status=task.status,
                    result=task.result,
                    error=error,
                )
            )

    return cases


@router.post("/{site_name}", response_model=CaseSchemaWithTaskInfo)
def create_site_case(
    site_name: str, driver: CTSMDriver = CTSMDriver.mct, db: Session = Depends(get_db)
) -> Any:
    """
    Create a case for the given site.
    """
    site = get_site_by_name(site_name)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    data = CaseSchemaCreate(
        name=site_name,
        compset=site.compset,
        res=site.res,
        data_url=site.url,
        driver=driver,
    )
    case = create_case(db=db, data=data)
    return case
