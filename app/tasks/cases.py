import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Union, cast

import requests

from app import crud, models, schemas
from app.core import settings
from app.db.session import SessionLocal
from app.utils.logger import logger
from app.utils.type_casting import to_bool

from .celery_app import celery_app


def to_namelist_value(
    variable_config: schemas.CaseVariableConfig, value: Union[int, float, str, bool]
) -> str:
    if variable_config.allow_multiple:
        assert isinstance(value, str)
        value_list: List[Union[int, float, str, bool]] = list(
            map(lambda v: v.strip(), value.split(","))
        )
    else:
        value_list = [value]

    namelist_value_list = []
    for v in value_list:
        match variable_config.type:
            case schemas.VariableType.char | schemas.VariableType.date:
                namelist_value_list.append(f"'{v}'")
            case schemas.VariableType.integer | schemas.VariableType.float:
                namelist_value_list.append(str(v))
            case schemas.VariableType.logical:
                namelist_value_list.append(".true." if to_bool(v) else ".false.")

    return ",".join(namelist_value_list)


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
    case_path = settings.CASES_ROOT / case.env["CASE_FOLDER_NAME"]

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

        for variable_dict in case.variables:
            assert isinstance(variable_dict, dict)
            variable = schemas.CaseVariable(**variable_dict)
            variable_config = schemas.CaseVariableConfig.get_variable_config(
                variable.name
            )

            if not variable_config:
                # This should only happen if an old case is being run with updated config
                raise Exception(f"Variable {variable.name} is not supported")

            value = (
                ",".join(map(lambda v: str(v), variable.value))
                if isinstance(variable.value, list)
                else variable.value
            )

            if variable_config.append_input_path:
                assert isinstance(value, str)
                value = str(cesm_data_root / Path(value))

            if variable_config.category == "ctsm_xml":
                xml_change_flags.append(f"{variable.name}={value}")
            elif (
                variable_config.category == "user_nl_clm"
                or variable_config.category == "user_nl_clm_history_file"
            ):
                with open(case_path / "user_nl_clm", "a") as f:
                    f.write(
                        f"{variable.name} = {to_namelist_value(variable_config, value)}\n"
                    )

        if xml_change_flags:
            run_cmd(
                case,
                ["./xmlchange", ",".join(xml_change_flags)],
                case_path,
                schemas.CaseStatus.UPDATED,
            )

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

    try:
        cesm_data_root = Path(case.env["CESMDATAROOT"])
    except KeyError:
        raise Exception("CESMDATAROOT environment variable is not set")

    run_cmd(case, ["./case.build"], case_path, schemas.CaseStatus.BUILT)

    run_cmd(
        case,
        ["./check_input_data", "--download"],
        case_path,
        schemas.CaseStatus.INPUT_DATA_READY,
    )

    fates_indices_dict = next(
        (v for v in case.variables if v["name"] == "included_pft_indices"), None
    )
    fates_param_path_dict = next(
        filter(lambda v: v["name"] == "fates_paramfile", case.variables), None
    )
    if fates_indices_dict:
        assert isinstance(fates_indices_dict, dict)
        fates_indices = cast(
            List[str], schemas.CaseVariable(**fates_indices_dict).value
        )

        if fates_param_path_dict:
            assert isinstance(fates_param_path_dict, dict)
            fates_param_path = schemas.CaseVariable(**fates_param_path_dict)

            fates_paramfile_variable_config = (
                schemas.CaseVariableConfig.get_variable_config("fates_paramfile")
            )

            if not fates_paramfile_variable_config:
                # This should only happen if an old case is being run with updated config
                raise Exception("Variable fates_paramfile is not supported")

            fates_param_path_str = fates_param_path.value
            assert isinstance(fates_param_path_str, str)

            if fates_paramfile_variable_config.append_input_path:
                fates_param_path_value = str(
                    cesm_data_root / Path(fates_param_path_str)
                )
            else:
                fates_param_path_value = fates_param_path_str

            for variable_dict in case.variables:
                assert isinstance(variable_dict, dict)
                variable = schemas.CaseVariable(**variable_dict)
                variable_config = schemas.CaseVariableConfig.get_variable_config(
                    variable.name
                )

                if not variable_config:
                    # This should only happen if an old case is being run with updated config
                    raise Exception(f"Variable {variable.name} is not supported")

                if variable_config.category == "fates_param":
                    param_values = cast(List[int], variable.value)
                    for idx, value in enumerate(param_values):
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
                                fates_param_path_value,
                                "--fout",
                                fates_param_path_value,
                                "--O",
                                "--pft",
                                str(idx + 1),
                                "--var",
                                variable.name,
                                "--value",
                                str(value),
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
                        ",".join(fates_indices),
                        "--fin",
                        fates_param_path_value,
                        "--fout",
                        output,
                    ],
                    None,
                    schemas.CaseStatus.FATES_INDICES_SET,
                )
                shutil.move(output, fates_param_path_value)
        else:
            raise Exception("Could not find FATES param file")

    run_cmd(case, ["./case.submit"], case_path, schemas.CaseStatus.SUBMITTED)

    with SessionLocal() as db:
        crud.case.update(
            db,
            db_obj=case,
            obj_in={"status": schemas.CaseStatus.SUBMITTED},
        )

    return "Case is ready"
