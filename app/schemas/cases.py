import hashlib
import json
import re
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from pydantic import BaseModel, parse_file_as, root_validator
from slugify import slugify

from app.core import settings
from app.tasks.celery_app import celery_app

from .constants import (
    CaseStatus,
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
    status: CaseStatus = CaseStatus.INITIALISED
    date_created: datetime = datetime.now()
    create_task_id: Optional[str] = None
    run_task_id: Optional[str] = None
    compset: str
    res: str
    variables: List[CaseVariable] = []
    fates_indices: Optional[str]
    env: Dict[str, str] = {}
    driver: CTSMDriver = CTSMDriver.mct
    data_url: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "compset": "2000_DATM%1PTGSWP3_CLM50%FATES_SICE_SOCN_MOSART_SGLC_SWAV",
                "res": "1x1_ALP1",
                "variables": [
                    {"name": "STOP_OPTION", "value": "nmonths"},
                    {"name": "STOP_N", "value": 3},
                ],
                "driver": CTSMDriver.mct,
                "data_url": "https://ns2806k.webs.sigma2.no/EMERALD/EMERALD_platform/inputdata_fates_platform/inputdata_version2.0.0_ALP1.tar",
            }
        }

    @staticmethod
    def generate_id(
        compset: str,
        res: str,
        variables: List[CaseVariable],
        data_url: str,
        driver: CTSMDriver,
        ctsm_tag: str,
    ) -> str:
        """
        Case id is a hash of the given arguments.
        This value is also used as the case path under `resources/cases/`.
        """
        hash_parts = "_".join(
            [
                compset,
                res,
                json.dumps(list(map(lambda v: v.dict(), variables))),
                data_url,
                driver,
                ctsm_tag,
            ]
        )
        case_id = bytes(hash_parts.encode("utf-8"))
        return hashlib.md5(case_id).hexdigest()

    @root_validator
    def validate_case(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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

            values["id"] = cls.generate_id(
                values["compset"],
                values["res"],
                validated_variables,
                values["data_url"],
                values["driver"],
                values["ctsm_tag"],
            )

            if values["name"]:
                case_folder_name = f"{values['id']}_{slugify(values['name'])}"
            else:
                case_folder_name = values["id"]

            cesm_data_root = str(settings.DATA_ROOT / case_folder_name)
            values["env"] = {
                "CESMDATAROOT": cesm_data_root,
                "CASE_FOLDER_NAME": case_folder_name,
            }

        return values


class CaseCreateDB(CaseBase):
    pass


class CaseUpdate(CaseBase):
    pass


class CaseWithTaskInfo(CaseBase):
    create_task: Task
    run_task: Task

    @staticmethod
    def get_case_with_task_info(case: "CaseModel") -> Optional["CaseWithTaskInfo"]:
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

        return CaseWithTaskInfo(**CaseBase.from_orm(case).dict(), **tasks)
