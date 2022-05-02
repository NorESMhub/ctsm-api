from typing import Any, List
from zipfile import ZipFile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.core import settings
from app.db.session import get_db

router = APIRouter()


# This must come before /{case_id} otherwise it will be handled by get_case.
@router.get("/variables", response_model=List[schemas.CaseVariableConfig])
def get_case_variables_config() -> Any:
    """
    Get the list of CTSM variables config.
    """
    return schemas.CaseVariableConfig.get_variables_config()


@router.get("/", response_model=List[schemas.CaseBase])
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
    if not case:
        return None

    task = tasks.run_case.delay(case)
    return schemas.CaseWithTaskInfo.get_case_with_task_info(
        crud.case.update(
            db,
            db_obj=case,
            obj_in={"status": schemas.CaseStatus.BUILDING, "run_task_id": task.id},
        )
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
    archive_name = settings.ARCHIVES_ROOT / f"{case_id}.zip"
    if archive_name.exists():
        return FileResponse(
            archive_name,
            headers={"Content-Disposition": f'attachment; filename="{case_id}.zip"'},
            media_type="application/zip",
        )

    case_path = settings.CASES_ROOT / case_id

    if not case_path.exists():
        raise HTTPException(status_code=404, detail="Case not found")

    with ZipFile(archive_name, "w") as zip_file:
        for f in case_path.rglob("*"):
            if not f.is_symlink():
                zip_file.write(f, arcname=f.relative_to(case_path))

    return FileResponse(
        archive_name,
        headers={"Content-Disposition": f'attachment; filename="{case_id}.zip"'},
        media_type="application/zip",
    )
