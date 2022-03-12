from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import get_settings
from app.crud import crud_case
from app.schemas import CaseSchema, CaseSchemaBase, CaseSchemaCreate, CaseWithTaskInfo
from app.tasks.cases import create_case_task

settings = get_settings()

router = APIRouter()


@router.get("/", response_model=List[CaseSchema])
def get_cases(
    db: Session = Depends(deps.get_db),
) -> Any:
    return crud_case.get_all(db)


@router.post("/", response_model=CaseWithTaskInfo)
def create_case(*, db: Session = Depends(deps.get_db), data: CaseSchemaBase) -> Any:
    obj_in = CaseSchemaCreate(**data.dict(), ctsm_tag=settings.CTSM_TAG)
    case = crud_case.create(db, obj_in=obj_in)
    task = create_case_task.delay(case)
    return CaseWithTaskInfo(
        item=CaseSchema.from_orm(case),
        task_id=task.id,
        status=task.status,
        result=task.result,
    )
