from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_case
from app.schemas import CaseSchemaCreate, CaseSchemaDB

router = APIRouter()


@router.get("/", response_model=List[CaseSchemaDB])
def get_cases(
    db: Session = Depends(deps.get_db),
) -> Any:
    return crud_case.get_all(db)


@router.post("/", response_model=CaseSchemaDB)
def create_case(*, db: Session = Depends(deps.get_db), case: CaseSchemaCreate) -> Any:
    return crud_case.create(db, obj_in=case)
