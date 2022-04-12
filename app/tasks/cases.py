import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import requests

from app import crud, models, schemas
from app.core import settings
from app.db.session import SessionLocal
from app.utils.logger import logger

from .celery_app import celery_app


def get_case_data_path(data_url: str) -> Path:
    return settings.DATA_ROOT / hashlib.md5(bytes(data_url.encode("utf-8"))).hexdigest()


def to_namelist_value(
    value: Union[int, float, str, bool], value_type: schemas.VariableType
) -> str:
    match value_type:
        case schemas.VariableType.char | schemas.VariableType.date:
            return f"'{value}'"
        case schemas.VariableType.integer | schemas.VariableType.float:
            return value
        case schemas.VariableType.logical:
            return ".true." if value else ".false."


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

    def run_cmd(
        cmd: List[str], cwd: Optional[Path], success_status: schemas.CaseStatus
    ):
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
                obj_in={"status": success_status},
            )

    run_cmd(
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
    run_cmd(["./case.setup"], case_path, schemas.CaseStatus.SETUP)

    if case.variables:
        xml_change_flags: List[str] = []
        for variable_dict in case.variables:
            assert isinstance(variable_dict, dict)
            variable = schemas.CaseVariable(**variable_dict)
            value = (
                ",".join(map(lambda v: str(v), variable.value))
                if isinstance(variable.value, list)
                else variable.value
            )
            if variable.category == "ctsm_xml":
                xml_change_flags.append(f"{variable.name}={value}")
            elif variable.category == "user_nl_clm":
                with open(case_path / "user_nl_clm", "a") as f:
                    f.write(
                        f"{variable.name} = {to_namelist_value(value, variable.type)}\n"
                    )

        if xml_change_flags:
            run_cmd(
                ["./xmlchange", ",".join(xml_change_flags)],
                case_path,
                schemas.CaseStatus.UPDATED,
            )

    cmds: List[Tuple[List[str], Optional[Path], schemas.CaseStatus]] = [
        (["./case.build"], case_path, schemas.CaseStatus.BUILT),
        (["./case.submit"], case_path, schemas.CaseStatus.SUBMITTED),
    ]

    for cmd, cwd, status in cmds:
        run_cmd(cmd, cwd, status)

    return "Case is ready"
