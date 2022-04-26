import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import requests

from app import crud, models, schemas
from app.core import settings
from app.db.session import SessionLocal
from app.utils.logger import logger

from .celery_app import celery_app


def to_namelist_value(
    value: Union[int, float, str, bool], value_type: schemas.VariableType
) -> str:
    match value_type:
        case schemas.VariableType.char | schemas.VariableType.date:
            return f"'{value}'"
        case schemas.VariableType.integer | schemas.VariableType.float:
            return str(value)
        case schemas.VariableType.logical:
            return ".true." if value else ".false."


def run_cmd(
    case: models.CaseModel,
    cmd: List[str],
    cwd: Optional[Path],
    success_status: schemas.CaseStatus,
) -> None:
    logger.info(f"Running {' '.join(cmd)}")
    start = time.time()

    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, env={**os.environ, **case.env}
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


@celery_app.task
def create_case(case: models.CaseModel) -> str:
    case_path = settings.CASES_ROOT / case.id

    try:
        cesm_data_root = Path(case.env["CESMDATAROOT"])
    except KeyError:
        raise Exception("CESMDATAROOT environment variable is not set")

    if not cesm_data_root.exists():
        response = requests.get(case.data_url, stream=True)
        with tarfile.open(fileobj=io.BytesIO(response.raw.read()), mode="r") as f:
            f.extractall(path=str(cesm_data_root))

    logger.info(
        f"Creating case {case.id} with the following attributes:\n"
        f"Path: {case_path}\n"
        f"Compset: {case.compset}\n"
        f"Res: {case.res}\n"
        f"Variables: {json.dumps(case.variables, indent=2)}\n"
        f"Driver: {case.driver}\n"
    )

    shutil.rmtree(case_path, ignore_errors=True)

    run_cmd(
        case,
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
    run_cmd(case, ["./case.setup"], case_path, schemas.CaseStatus.SETUP)

    if case.variables:
        xml_change_flags: List[str] = []

        fates_indices: Optional[str] = None
        fates_param_path: Optional[Path] = None
        fates_params: List[Tuple[str, schemas.VariableValue]] = []

        for variable_dict in case.variables:
            assert isinstance(variable_dict, dict)
            variable = schemas.CaseVariable(**variable_dict)
            value = (
                ",".join(map(lambda v: str(v), variable.value))
                if isinstance(variable.value, list)
                else variable.value
            )
            if variable.append_input_path:
                # TODO Should inputdata be parameterized?
                value = cesm_data_root / "inputdata" / value

            if variable.name == "included_pft_indices":
                fates_indices = value
            else:
                if variable.category == "ctsm_xml":
                    xml_change_flags.append(f"{variable.name}={value}")
                elif variable.category == "user_nl_clm":
                    with open(case_path / "user_nl_clm", "a") as f:
                        f.write(
                            f"{variable.name} = {to_namelist_value(value, variable.type)}\n"
                        )
                    if variable.name == "fates_paramfile":
                        fates_param_path = value
                elif variable.category == "fates_param":
                    fates_params.append((variable.name, value))

        if xml_change_flags:
            run_cmd(
                case,
                ["./xmlchange", ",".join(xml_change_flags)],
                case_path,
                schemas.CaseStatus.UPDATED,
            )

        if fates_indices:
            if fates_param_path:
                for fates_param, value_list in fates_params:
                    assert isinstance(value_list, str)
                    for idx, value in enumerate(value_list.split(",")):
                        run_cmd(
                            case,
                            [
                                str(
                                    settings.CTSM_ROOT
                                    / "components"
                                    / "clm"
                                    / "src"
                                    / "fates"
                                    / "tools"
                                    / "modify_fates_paramfile.py"
                                ),
                                "--fin",
                                str(fates_param_path),
                                "--fout",
                                str(fates_param_path),
                                "--O",
                                "--pft",
                                str(idx + 1),
                                "--var",
                                fates_param,
                                "--value",
                                value.strip(),
                            ],
                            None,
                            schemas.CaseStatus.FATES_PARAMS_UPDATED,
                        )

                (_, output) = tempfile.mkstemp()
                run_cmd(
                    case,
                    [
                        str(
                            settings.CTSM_ROOT
                            / "components"
                            / "clm"
                            / "src"
                            / "fates"
                            / "tools"
                            / "FatesPFTIndexSwapper.py"
                        ),
                        "--pft-indices",
                        fates_indices,
                        "--fin",
                        str(fates_param_path),
                        "--fout",
                        output,
                    ],
                    None,
                    schemas.CaseStatus.FATES_INDICES_SET,
                )
                shutil.move(output, fates_param_path)
            else:
                raise Exception("Could not find FATES param file")

    with SessionLocal() as db:
        crud.case.update(
            db,
            db_obj=case,
            obj_in={"status": schemas.CaseStatus.CONFIGURED},
        )

    return "Case is configured"


@celery_app.task
def run_case(case: models.CaseModel) -> str:
    case_path = settings.CASES_ROOT / case.id

    cmds: List[Tuple[List[str], Optional[Path], schemas.CaseStatus]] = [
        (["./case.build"], case_path, schemas.CaseStatus.BUILT),
        (["./case.submit"], case_path, schemas.CaseStatus.SUBMITTED),
    ]

    for cmd, cwd, status in cmds:
        run_cmd(case, cmd, cwd, status)

    with SessionLocal() as db:
        crud.case.update(
            db,
            db_obj=case,
            obj_in={"status": schemas.CaseStatus.SUBMITTED},
        )

    return "Case is ready"
