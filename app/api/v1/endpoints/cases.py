import os
import shutil
import tarfile
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import ARCHIVES_ROOT, CASES_ROOT, get_settings
from app.crud import crud_case
from app.db.session import get_db
from app.schemas import (
    CaseSchema,
    CaseSchemaCreate,
    CaseSchemaCreateDB,
    CaseSchemaWithTaskInfo,
)
from app.tasks import celery_app, create_case_task
from app.utils.cases import get_case_id

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
    case_path = get_case_id(data.compset, data.res, data.driver, data.data_url)
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
        shutil.rmtree(CASES_ROOT / case_id)
    if (ARCHIVES_ROOT / f"{case_id}.tar.gz").exists():
        os.remove(ARCHIVES_ROOT / f"{case_id}.tar.gz")
    return crud_case.remove(db, id=case_id)


@router.get("/{case_id}/download")
def download_case(case_id: str) -> Any:
    """
    Download a compressed tarball of the case with the given id.
    """
    archive_name = ARCHIVES_ROOT / f"{case_id}.tar.gz"
    if archive_name.exists():
        return FileResponse(
            archive_name,
            headers={"Content-Disposition": f'attachment; filename="{case_id}.tar.gz"'},
            media_type="application/x-gzip",
        )

    if not (CASES_ROOT / case_id).exists():
        raise HTTPException(status_code=404, detail="Case not found")

    with tarfile.open(archive_name, mode="w:gz") as tar:
        for f in (CASES_ROOT / case_id).iterdir():
            if not f.is_symlink():
                tar.add(f, arcname=f.name)

    return FileResponse(
        archive_name,
        headers={"Content-Disposition": f'attachment; filename="{case_id}.tar.gz"'},
        media_type="application/x-gzip",
    )
