from typing import Any, List
from zipfile import ZipFile

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, schemas, tasks
from app.core import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/ctsm-info", response_model=schemas.CTSMInfo)
def get_ctsm_info() -> Any:
    return schemas.CTSMInfo.get_ctsm_info()


# This must come before /{case_id} otherwise it will be handled by get_case.
@router.get("/variables", response_model=List[schemas.CaseVariableConfig])
def get_case_variables_config() -> Any:
    """
    Get the list of CTSM variables config.
    """
    return schemas.CaseVariableConfig.get_variables_config()


@router.get("/", response_model=List[schemas.CaseWithTaskInfo])
def get_cases(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all cases.
    """
    return [
        schemas.CaseWithTaskInfo.get_case_with_task_info(case, site)
        for (case, site) in crud.case.get_all_cases_with_site(db)
    ]


@router.get("/{case_id}", response_model=schemas.CaseWithTaskInfo)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the case with the given id.
    """
    case_and_site = crud.case.get_case_with_site(db, id=case_id)
    if not case_and_site:
        return None
    (case, site) = case_and_site
    return schemas.CaseWithTaskInfo.get_case_with_task_info(case, site)


@router.post("/", response_model=schemas.CaseWithTaskInfo)
def create_case(
    case_attrs: schemas.CaseBase = Body(...),
    data_file: UploadFile | None = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new case with the given parameters.
    """
    try:
        case = crud.case.create(db, obj_in=case_attrs, data_file=data_file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    case_with_site = crud.case.get_case_with_site(db, id=case.id)
    if not case_with_site:
        # This should never happen.
        raise HTTPException(status_code=400, detail="Case not found")
    (case, site) = case_with_site
    return schemas.CaseWithTaskInfo.get_case_with_task_info(case, site)


@router.post("/{case_id}", response_model=schemas.CaseWithTaskInfo)
def run_case(case_id: str, db: Session = Depends(get_db)) -> Any:
    case_and_site = crud.case.get_case_with_site(db, id=case_id)
    if not case_and_site:
        return None

    (case, site) = case_and_site

    task = tasks.run_case.delay(case)
    return schemas.CaseWithTaskInfo.get_case_with_task_info(
        crud.case.update(
            db,
            db_obj=case,
            obj_in={"status": schemas.CaseRunStatus.BUILDING, "run_task_id": task.id},
        ),
        site,
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
def download_case(case_id: str, db: Session = Depends(get_db)) -> Any:
    """
    Download a compressed tarball of the case with the given id.
    """
    case_and_site = crud.case.get_case_with_site(db, id=case_id)

    if not case_and_site:
        return None

    (case, site) = case_and_site

    case_folder_name = case.env["CASE_FOLDER_NAME"]

    archive_name = settings.ARCHIVES_ROOT / f"{case_folder_name}.zip"
    if archive_name.exists():
        return FileResponse(
            archive_name,
            headers={
                "Content-Disposition": f'attachment; filename="{case_folder_name}.zip"'
            },
            media_type="application/zip",
        )

    case_path = settings.CASES_ROOT / case_folder_name

    if not case_path.exists():
        raise HTTPException(status_code=404, detail="Case not found")

    with ZipFile(archive_name, "w") as zip_file:
        for f in case_path.rglob("*"):
            if not f.is_symlink():
                zip_file.write(f, arcname=f.relative_to(case_path))

    return FileResponse(
        archive_name,
        headers={
            "Content-Disposition": f'attachment; filename="{case_folder_name}.zip"'
        },
        media_type="application/zip",
    )
