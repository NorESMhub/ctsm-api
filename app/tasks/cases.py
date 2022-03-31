import io
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from app import crud, models, schemas
from app.core import settings
from app.db.session import SessionLocal
from app.utils.cases import get_case_data_path
from app.utils.logger import logger

from .celery_app import celery_app


@celery_app.task
def create_case_task(case: models.CaseModel) -> str:
    case_path = settings.CASES_ROOT / case.id
    input_data_path = get_case_data_path(case.data_url)
    env = {
        "CESMDATAROOT": str(input_data_path),
    }

    if not input_data_path.exists():
        response = requests.get(case.data_url, stream=True)
        with tarfile.open(fileobj=io.BytesIO(response.raw.read()), mode="r") as f:
            f.extractall(path=str(input_data_path))

    logger.info(
        f"Creating case {case.id} with the following attributes:\n"
        f"Path: {case_path}\n"
        f"Compset: {case.compset}\n"
        f"Res: {case.res}\n"
        f"Variables: {json.dumps(case.variables, indent=2)}\n"
        f"Driver: {case.driver}\n"
    )

    shutil.rmtree(case_path, ignore_errors=True)

    cmds: List[Tuple[List[str], Optional[Path], schemas.CaseStatus]] = [
        (
            [
                str(settings.CTSM_ROOT / "cime" / "scripts" / "create_newcase"),
                "--case",
                str(case_path),
                "--compset",
                case.compset,
                "--res",
                case.res,
                "--driver",
                case.driver,
                "--machine",
                settings.MACHINE_NAME,
                "--run-unsupported",
                "--handle-preexisting-dirs",
                "r",
            ],
            None,
            schemas.CaseStatus.CREATED,
        )
    ]
    if case.variables:
        xml_change_flags = []
        for key, variables in case.variables.items():
            if key not in settings.CASE_ALLOWED_VARS:
                logger.warn(f"Variable {key} is not allowed")
                continue
            xml_change_flags.append(f"{key}={variables}")

        cmds.append(
            (
                ["./xmlchange", ",".join(xml_change_flags)],
                case_path,
                schemas.CaseStatus.UPDATED,
            ),
        )

    cmds.extend(
        [
            (["./case.setup"], case_path, schemas.CaseStatus.SETUP),
            (["./case.build"], case_path, schemas.CaseStatus.BUILT),
            (["./case.submit"], case_path, schemas.CaseStatus.SUBMITTED),
        ]
    )

    for cmd, cwd, status in cmds:
        logger.info(f"Running {' '.join(cmd)}")
        start = time.time()

        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, env={**os.environ, **env}
        )

        logger.info(f"Finished {cmd[0]} in {time.time() - start} seconds")

        if proc.returncode != 0:
            raise Exception(proc.stderr.decode("utf-8").strip())

        with SessionLocal() as db:
            crud.case.update(
                db,
                db_obj=case,
                obj_in={"status": status},
            )

    return "Case is ready"
