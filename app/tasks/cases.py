import subprocess

from celery.states import FAILURE

from app.core.config import CASES_ROOT, CTSM_ROOT, get_settings
from app.models import CaseModel
from app.utils.logger import logger

from .celery_app import celery_app

settings = get_settings()


@celery_app.task
def create_case_task(case: CaseModel) -> None:
    logger.info("Creating case {}".format(case.id))
    proc = subprocess.run(
        [
            CTSM_ROOT / "cime" / "scripts" / "create_newcase",
            "--case",
            CASES_ROOT / f"{case.id}_{case.compset}_{case.res}_{settings.CTSM_TAG}",
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
    if proc.returncode != 0:
        logger.error("Failed to create case {}".format(case.id))
        logger.error(proc.stderr.decode("utf-8"))
        create_case_task.update_state(state=FAILURE)
