import tarfile
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.core import settings
from app.db.session import get_db

router = APIRouter()


# This must come before /{case_id} otherwise it will be handled by get_case.
@router.get("/variables", response_model=List[schemas.CaseVariableConfig])
def get_case_allowed_vars() -> Any:
    """
    Get the list of CTSM variables config that can be changed by user.
    """
    return schemas.CaseVariableConfig.get_variables_config()


@router.get("/", response_model=List[schemas.CaseDB])
def get_cases(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases.
    """
    return crud.case.get_all(db)


@router.get("/{case_id}", response_model=schemas.CaseWithTaskInfo)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the case with the given id.
    """
    case = crud.case.get(db, id=case_id)
    if not case:
        return None
    return schemas.CaseWithTaskInfo.get_case_with_task_info(case)


@router.post("/", response_model=schemas.CaseWithTaskInfo)
def create_case(data: schemas.CaseBase, db: Session = Depends(get_db)) -> Any:
    """
    Create a new case with the given parameters.
    """
    case = crud.case.create(db, obj_in=data)
    return schemas.CaseWithTaskInfo.get_case_with_task_info(case)


@router.post("/{case_id}", response_model=schemas.CaseWithTaskInfo)
def run_case(case_id: str, db: Session = Depends(get_db)) -> Any:
    case = crud.case.get(db, id=case_id)
    task = tasks.run_case.delay(case.id)
    return crud.case.update(
        db, case, {"status": schemas.CaseStatus.BUILDING, "run_task_id": task.id}
    )


@router.delete("/{case_id}")
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete the case with the given id.
    """
    return crud.case.remove(db, id=case_id)


@router.get("/{case_id}/download")
def download_case(case_id: str) -> Any:
    """
    Download a compressed tarball of the case with the given id.
    """
    archive_name = settings.ARCHIVES_ROOT / f"{case_id}.tar.gz"
    if archive_name.exists():
        return FileResponse(
            archive_name,
            headers={"Content-Disposition": f'attachment; filename="{case_id}.tar.gz"'},
            media_type="application/x-gzip",
        )

    if not (settings.CASES_ROOT / case_id).exists():
        raise HTTPException(status_code=404, detail="Case not found")

    with tarfile.open(archive_name, mode="w:gz") as tar:
        for f in (settings.CASES_ROOT / case_id).iterdir():
            if not f.is_symlink():
                tar.add(f, arcname=f.name)

    return FileResponse(
        archive_name,
        headers={"Content-Disposition": f'attachment; filename="{case_id}.tar.gz"'},
        media_type="application/x-gzip",
    )
