import shutil
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import CASES_ROOT, get_settings
from app.crud import crud_case
from app.db.session import get_db
from app.schemas import (
    CaseSchema,
    CaseSchemaCreate,
    CaseSchemaCreateDB,
    CaseSchemaWithTaskInfo,
)
from app.tasks import celery_app, create_case_task
from app.utils.sites import get_site_id

settings = get_settings()

router = APIRouter()


@router.get("/", response_model=List[CaseSchema])
def get_cases(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases.
    """
    return crud_case.get_all(db)


@router.get("/{case_id}", response_model=CaseSchemaWithTaskInfo)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the case with the given id.
    """
    case = crud_case.get(db, id=case_id)

    if not case:
        return None

    task = celery_app.AsyncResult(case.task_id)
    error = task.traceback.strip().split("\n")[-1] if task.traceback else None

    return CaseSchemaWithTaskInfo(
        case=case, task_id=task.id, status=task.status, result=task.result, error=error
    )


@router.post("/", response_model=CaseSchemaWithTaskInfo)
def create_case(*, data: CaseSchemaCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new case with the given parameters.
    """
    case_path = get_site_id(data.compset, data.res, data.driver, data.data_url)
    case = crud_case.get(db, id=case_path)

    if case:
        if (CASES_ROOT / case.id).exists():
            task = celery_app.AsyncResult(case.task_id)
        else:
            task = create_case_task.delay(case)
    else:
        obj_in = CaseSchemaCreateDB(
            **data.dict(), id=case_path, ctsm_tag=settings.CTSM_TAG
        )
        case = crud_case.create(db, obj_in=obj_in)
        task = create_case_task.delay(case)
        case = crud_case.update(db, db_obj=case, obj_in={"task_id": task.id})

    crud_case.update(db, db_obj=case, obj_in={"task_id": task.id})
    error = task.traceback.strip().split("\n")[-1] if task.traceback else None

    return CaseSchemaWithTaskInfo(
        case=CaseSchema.from_orm(case),
        task_id=task.id,
        status=task.status,
        result=task.result,
        error=error,
    )


@router.delete("/{case_id}")
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete the case with the given id.
    """
    if (CASES_ROOT / case_id).exists():
        shutil.rmtree((CASES_ROOT / case_id))
    return crud_case.remove(db, id=case_id)
