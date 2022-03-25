import os
import shutil
import tarfile
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import ARCHIVES_ROOT, CASES_ROOT, get_settings
from app.crud import crud_case
from app.db.session import get_db
from app.tasks.cases import create_case_task
from app.utils.cases import get_case_id

settings = get_settings()

router = APIRouter()


@router.get("/", response_model=List[schemas.CaseDB])
def get_cases(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases.
    """
    return crud_case.get_all(db)


@router.get("/{case_id}", response_model=schemas.CaseWithTaskInfo)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the case with the given id.
    """
    return crud_case.get_case_with_task_info(db, case_id=case_id)


@router.post("/", response_model=schemas.CaseWithTaskInfo)
def create_case(data: schemas.CaseBase, db: Session = Depends(get_db)) -> Any:
    """
    Create a new case with the given parameters.
    """
    obj_in = schemas.CaseCreateDB(**data.dict(), id="", ctsm_tag=settings.CTSM_TAG)
    case_id = get_case_id(obj_in)
    case__with_task_info = crud_case.get_case_with_task_info(db, case_id=case_id)

    if case__with_task_info:
        return case__with_task_info

    obj_in.id = case_id
    case = crud_case.create(db, obj_in=obj_in)
    task = create_case_task.delay(case)
    case = crud_case.update(db, db_obj=case, obj_in={"task_id": task.id})
    error = task.traceback.strip().split("\n")[-1] if task.traceback else None

    return schemas.CaseWithTaskInfo(
        case=schemas.CaseDB.from_orm(case),
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
