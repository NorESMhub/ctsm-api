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

settings = get_settings()

router = APIRouter()


@router.get("/", response_model=List[CaseSchema])
def get_sites(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases
    """
    return crud_case.get_all(db)


@router.get("/{case_id}", response_model=CaseSchemaWithTaskInfo)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases
    """
    case = crud_case.get(db, case_id)

    if not case:
        return None

    task = celery_app.AsyncResult(case.task_id)
    return CaseSchemaWithTaskInfo(
        case=case, task_id=task.id, status=task.status, result=task.result
    )


@router.post("/", response_model=CaseSchemaWithTaskInfo)
def create_case(*, db: Session = Depends(get_db), data: CaseSchemaCreate) -> Any:
    case_path = crud_case.get_case_path(data.compset, data.res, data.driver)
    case = crud_case.get(db, case_path)

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

    return CaseSchemaWithTaskInfo(
        case=CaseSchema.from_orm(case),
        task_id=task.id,
        status=task.status,
        result=task.result,
    )


@router.delete("/{case_id}")
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a case
    """
    if (CASES_ROOT / case_id).exists():
        shutil.rmtree((CASES_ROOT / case_id))
    return crud_case.remove(db, id=case_id)
