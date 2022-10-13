import hashlib
import io
import json
import re
import shutil
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Union, cast
from zipfile import ZipFile

import requests
from fastapi import UploadFile
from pydantic import BaseModel, Field, parse_file_as, root_validator
from slugify import slugify

from app.core import settings
from app.tasks.celery_app import celery_app

from .constants import (
    CaseCreateStatus,
    CaseRunStatus,
    CTSMDriver,
    VariableCategory,
    VariableType,
    VariableValue,
)
from .tasks import Task

if TYPE_CHECKING:
    from app.models import CaseModel


class CTSMInfo(BaseModel):
    model: str
    version: str
    drivers: List[CTSMDriver]

    @staticmethod
    def get_ctsm_info() -> "CTSMInfo":
        return CTSMInfo(
            model=settings.CTSM_REPO,
            version=settings.CTSM_TAG,
            drivers=settings.CTSM_DRIVERS,
        )


class VariableChoice(BaseModel):
    value: VariableValue
    label: str


class VariableValidation(BaseModel):
    min: Optional[Union[int, float]]
    max: Optional[Union[int, float]]
    pattern: Optional[str]
    pattern_error: Optional[str]
    choices: Optional[List[VariableChoice]]


class CaseVariableDescription(BaseModel):
    summary: str
    details: Optional[str]
    url: Optional[str]


class CaseVariableConfig(BaseModel):
    name: str
    label: Optional[str]
    category: VariableCategory
    type: VariableType
    description: Optional[CaseVariableDescription]
    readonly: bool = False
    hidden: Optional[bool] = False
    allow_multiple: bool = False
    allow_custom: bool = False
    validation: Optional[VariableValidation]
    default: Optional[VariableValue]
    placeholder: Optional[str]
    append_input_path = False

    class Config:
        smart_union = True

    @classmethod
    @lru_cache()
    def get_variables_config(cls) -> List["CaseVariableConfig"]:
        return (
            parse_file_as(List[CaseVariableConfig], settings.VARIABLES_CONFIG_PATH)
            if settings.VARIABLES_CONFIG_PATH.exists()
            else []
        )

    @classmethod
    @lru_cache()
    def get_variable_config(cls, variable_name: str) -> Optional["CaseVariableConfig"]:
        return next(
            (
                variable_config
                for variable_config in cls.get_variables_config()
                if variable_config.name == variable_name
            ),
            None,
        )


class CaseVariable(BaseModel):
    name: str
    value: VariableValue

    class Config:
        smart_union = True


class CaseBase(BaseModel):
    id: str = ""
    name: str = ""
    ctsm_tag: str = settings.CTSM_TAG
    status: CaseCreateStatus | CaseRunStatus = CaseCreateStatus.INITIALISED
    date_created: datetime = Field(default_factory=datetime.now)
    create_task_id: Optional[str] = None
    run_task_id: Optional[str] = None
    compset: str
    lat: Optional[float]
    lon: Optional[float]
    variables: List[CaseVariable] = []
    fates_indices: Optional[str]
    env: Dict[str, str] = {}
    driver: CTSMDriver = CTSMDriver.nuopc
    data_url: Optional[str]
    data_digest: str = ""

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "compset": "2000_DATM%GSWP3v1_CLM51%FATES_SICE_SOCN_MOSART_SGLC_SWAV",
                "variables": [
                    {"name": "STOP_OPTION", "value": "nmonths"},
                    {"name": "STOP_N", "value": 3},
                ],
                "driver": CTSMDriver.nuopc,
                "data_url": "https://ns2806k.webs.sigma2.no/EMERALD/EMERALD_platform/inputdata_noresm_landsites/v1.0.0/default/ALP1.zip",
            }
        }

    @classmethod
    def __get_validators__(cls) -> Generator[Any, None, None]:
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

    def set_id(self) -> None:
        """
        Case id is a hash of the given arguments.
        This value is also used as the case path under `resources/cases/`.
        """
        hash_parts = "_".join(
            [
                self.name,
                self.compset,
                json.dumps(list(map(lambda v: v.dict(), self.variables))),
                self.driver,
                self.ctsm_tag,
                self.data_digest,
            ]
        )
        self.id = hashlib.md5(bytes(hash_parts.encode("utf-8"))).hexdigest()

        if self.name:
            case_folder_name = f"{self.id}_{slugify(self.name)}"
        else:
            case_folder_name = self.id

        case_data_root = str(settings.DATA_ROOT / case_folder_name)
        self.env.update(
            {
                "CASE_DATA_ROOT": case_data_root,
                "CASE_FOLDER_NAME": case_folder_name,
            }
        )

    @root_validator
    def validate_case(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values["driver"] not in settings.CTSM_DRIVERS:
            raise ValueError(f"Driver {values['driver']} not supported")

        for required_field in ["compset"]:
            if required_field not in values:
                raise ValueError(f"Missing required field: {required_field}")

        if not values["id"]:
            variables = values["variables"]
            validated_variables = []
            errors = None

            for variable in variables:
                if variable.name == "user_nl_clm_extra":
                    validated_variables.append(variable)
                    continue

                variable_config = CaseVariableConfig.get_variable_config(variable.name)

                if not variable_config:
                    continue

                value = variable.value

                if variable_config.name == "included_pft_indices":
                    fates_indices = cast(
                        List[str], value.split(",") if isinstance(value, str) else value
                    )
                    try:
                        value = [int(index.strip()) for index in fates_indices]
                    except ValueError:
                        errors = "Invalid fates index: {}".format(value)
                        continue

                if variable_config.allow_multiple:
                    if not isinstance(value, list):
                        value = [value]
                else:
                    if isinstance(value, list):
                        if len(value) > 1:
                            errors = f"Variable {variable.name} is not allowed to have multiple values."
                            continue
                    else:
                        value = [value]

                assert isinstance(value, list)

                validated_values = []
                for v in value:
                    validated_value: Optional[Union[int, float, str, bool]] = None
                    if variable_config.type == "char" or variable_config.type == "date":
                        try:
                            validated_value = str(v)
                        except ValueError:
                            errors = f"Variable {variable.name} is not valid string."
                            continue
                    elif variable_config.type == "integer":
                        try:
                            validated_value = int(v)
                        except ValueError:
                            errors = f"Variable {variable.name} is not valid integer"
                            continue
                    elif variable_config.type == "float":
                        try:
                            validated_value = float(v)
                        except ValueError:
                            errors = f"Variable {variable.name} is not valid float"
                            continue
                    elif variable_config.type == "logical":
                        try:
                            validated_value = bool(v)
                        except ValueError:
                            errors = f"Variable {variable.name} is not valid boolean"
                            continue

                    if validated_value is None:
                        errors = f"Variable {variable.name} is not valid."
                        continue

                    if variable_config.validation:
                        if (
                            not variable_config.allow_custom
                            and variable_config.validation.choices
                        ):
                            if not next(
                                filter(
                                    lambda c: c.value == validated_value,  # noqa: B023
                                    variable_config.validation.choices,
                                ),
                                None,
                            ):
                                errors = f"{variable.value} is not a valid choice for {variable.name}."
                                continue
                        else:
                            if variable_config.validation.min:
                                if (
                                    type(validated_value) != int
                                    or type(validated_value) != float
                                    or validated_value < variable_config.validation.min
                                ):
                                    errors = f"{variable.value} is less than minimum value for {variable.name}."
                                    continue
                            if variable_config.validation.max:
                                if (
                                    type(validated_value) != int
                                    or type(validated_value) != float
                                    or validated_value > variable_config.validation.max
                                ):
                                    errors = f"{variable.value} is greater than maximum value for {variable.name}."
                                    continue
                            if variable_config.validation.pattern:
                                if type(validated_value) != str or not re.match(
                                    variable_config.validation.pattern, validated_value
                                ):
                                    if variable_config.validation.pattern_error:
                                        errors = (
                                            variable_config.validation.pattern_error
                                        )
                                    else:
                                        errors = f"{variable.value} does not match pattern for {variable.name}."
                                    continue

                    validated_values.append(validated_value)

                variable.value = (
                    validated_values
                    if variable_config.allow_multiple
                    else validated_values[0]
                )
                validated_variables.append(variable)

            if errors:
                raise ValueError(errors)

            validated_variables.sort(key=lambda v: v.name)

            values["variables"] = validated_variables

            values["ctsm_tag"] = settings.CTSM_TAG

        return values

    def validate_data_file(self, data_file: UploadFile | None) -> None:
        if data_file and self.data_url:
            raise ValueError(
                "You must provide either a data file or the data_url attribute, not both."
            )

        if self.data_url:
            response = requests.get(self.data_url, stream=True)
            content_type = response.headers.get("content-type", "")
            data_file_obj = response.raw.read()
        elif data_file:
            content_type = data_file.content_type
            data_file_obj = data_file.file.read()
        else:
            raise ValueError(
                "You must provide either a data file or the data_url attribute."
            )

        if "application/zip" not in content_type.lower():
            raise ValueError("Data must be a valid zip file.")

        self.data_digest = hashlib.md5(data_file_obj).hexdigest()
        self.set_id()

        data_output_path = Path(self.env["CASE_DATA_ROOT"])
        if data_output_path.exists():
            shutil.rmtree(data_output_path)
        data_output_path.mkdir(parents=True)

        with ZipFile(io.BytesIO(data_file_obj), "r") as zf:
            extract_path = Path(data_output_path)
            zf.extractall(extract_path)

        try:
            with open(extract_path / "user_mods" / "shell_commands", "r") as f:
                shell_commands = f.read()
        except FileNotFoundError:
            raise ValueError("Data must contain a user_mods/shell_commands file.")

        lon = re.search(r"PTS_LON=(?P<lon>\d+(?:\.\d+)?)", shell_commands)
        lat = re.search(r"PTS_LAT=(?P<lat>\d+(?:\.\d+)?)", shell_commands)

        if not lon or not lat:
            raise ValueError("Data must contain PTS_LON and PTS_LAT variables.")

        self.lon = float(lon.group("lon"))
        self.lat = float(lat.group("lat"))

        with open(extract_path / "user_mods" / "shell_commands", "w") as f:
            # Write a new shell_commands file to avoid running any malicious code
            f.write(f"./xmlchange CLM_USRDAT_DIR={extract_path}\n")
            f.write(f"./xmlchange PTS_LON={lon.group('lon')}\n")
            f.write(f"./xmlchange PTS_LAT={lat.group('lat')}\n")


class CaseDBCreate(CaseBase):
    pass


class CaseDBUpdate(CaseBase):
    pass


class Case(CaseBase):
    site: Optional[str] = None


class CaseWithTaskInfo(Case):
    create_task: Task
    run_task: Task

    @staticmethod
    def get_case_with_task_info(
        case: "CaseModel", site: Optional[str] = None
    ) -> Optional["CaseWithTaskInfo"]:
        tasks = {}
        for task_id_type in ["create_task_id", "run_task_id"]:
            task_id = getattr(case, task_id_type)
            task_dict = {"task_id": None, "status": None, "result": None, "error": None}
            if task_id:
                task = celery_app.AsyncResult(task_id)
                task_dict = {
                    "task_id": task.id,
                    "status": task.status,
                    "result": task.result,
                    "error": task.traceback.strip().split("\n")[-1]
                    if task.traceback
                    else None,
                }
            tasks[task_id_type[:-3]] = task_dict

        case_dict = CaseBase.from_orm(case).dict()
        case_dict["site"] = site
        return CaseWithTaskInfo(**case_dict, **tasks)
