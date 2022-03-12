import subprocess

from celery.states import FAILURE

from app.core.config import CASES_ROOT, CTSM_ROOT, get_settings
from app.crud import crud_case
from app.db.session import SessionLocal
from app.models import CaseModel
from app.schemas import CaseStatus
from app.utils.logger import logger

from .celery_app import celery_app

settings = get_settings()


@celery_app.task
def create_case_task(case: CaseModel) -> None:

    logger.info(
        f"Creating case {case.id} with the following attributes:\n"
        f"Name: {case.name}\n"
        f"Path: {case.id}\n"
        f"Compset: {case.compset}\n"
        f"Res: {case.res}\n"
        f"Driver: {case.driver}\n"
    )

    proc = subprocess.run(
        [
            CTSM_ROOT / "cime" / "scripts" / "create_newcase",
            "--case",
            CASES_ROOT / case.id,
            "--compset",
            case.compset,
            "--res",
            case.res,
            "--driver",
            case.driver,
            "--machine",
            "container",
            "--run-unsupported",
            "--handle-preexisting-dirs",
            "r",
        ],
        capture_output=True,
    )

    if proc.returncode == 0:
        with SessionLocal() as db:
            crud_case.update(db, db_obj=case, obj_in={"status": CaseStatus.created})
    else:
        logger.error("Failed to create case {}".format(case.id))
        logger.error(proc.stderr.decode("utf-8"))
        create_case_task.update_state(state=FAILURE)
