import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, parse_file_as, validator

from app import models, tasks
from app.core import settings

from .tasks import Task


class VariableType(str, Enum):
    """The types are based on what is used in CTSM xml files,
    except for date, which is char in yyyy-mm-dd format in CTSM."""

    char = "char"
    integer = "integer"
    float = "float"
    logical = "logical"
    date = "date"


VARIABLE_VALUE = Union[str, int, float, bool, List[Union[str, int, float, bool]]]


class VariableCategory(str, Enum):
    ctsm_xml = "ctsm_xml"
    ctsm_nl_ln = "ctsm_nl_lnd"
    fates = "fates"


class VariableValidation(BaseModel):
    min: Optional[Union[int, float]]
    max: Optional[Union[int, float]]
    pattern: Optional[str]
    choices: Optional[List[Union[str, int, float]]]


class CaseVariableConfig(BaseModel):
    name: str
    category: VariableCategory
    type: VariableType
    description: Optional[str]
    readonly: bool = False
    allow_multiple: bool = False
    validation: Optional[VariableValidation]
    default: Optional[VARIABLE_VALUE]

    @classmethod
    def get_variables_config(cls) -> List["CaseVariableConfig"]:
        return (
            parse_file_as(List[CaseVariableConfig], settings.VARIABLES_CONFIG_PATH)
            if settings.VARIABLES_CONFIG_PATH.exists()
            else []
        )


class CaseVariable(BaseModel):
    name: str
    value: VARIABLE_VALUE

    # Category is populated by CaseBase variables validator.
    # All other schemas that use this class should use CaseBase for validation.
    category: Optional[VariableCategory] = None


class CTSMDriver(str, Enum):
    """The driver to use with CTSM create_newcase script."""

    nuopc = "nuopc"
    mct = "mct"


class CaseStatus(str, Enum):
    INITIALISED = "INITIALISED"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SETUP = "SETUP"
    BUILT = "BUILT"
    SUBMITTED = "SUBMITTED"


class CaseBase(BaseModel):
    compset: str
    res: str
    variables: List[CaseVariable] = []
    driver: CTSMDriver = CTSMDriver.mct
    data_url: str

    class Config:
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

    @validator("variables", always=True)
    def validate_variables(cls, variables: List[CaseVariable]) -> List[CaseVariable]:
        variables_config = CaseVariableConfig.get_variables_config()
        validated_variables = []
        errors = None

        for variable in variables:
            variable_config = next(
                filter(lambda config: config.name == variable.name, variables_config),
                None,
            )

            if not variable_config:
                errors = f"Variable {variable.name} is not allowed."
                continue

            value = variable.value
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
                validated_value: Optional[Union[str, int, float, bool]] = None
                if variable_config.type == "char":
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

                if not validated_value:
                    errors = f"Variable {variable.name} is not valid."
                    continue

                if variable_config.validation:
                    if variable_config.validation.choices:
                        if validated_value not in variable_config.validation.choices:
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
                                errors = f"{variable.value} does not match pattern for {variable.name}."
                                continue

                validated_values.append(validated_value)

            variable.value = validated_values
            variable.category = variable_config.category
            validated_variables.append(variable)

        if errors:
            raise ValueError(errors)

        validated_variables.sort(key=lambda v: v.name)

        return validated_variables


class CaseDB(CaseBase):
    id: str
    ctsm_tag: str
    status: CaseStatus = CaseStatus.INITIALISED
    date_created: datetime = datetime.now()
    task_id: Optional[str] = None

    class Config:
        orm_mode = True


class CaseCreateDB(CaseDB):
    pass


class CaseUpdate(CaseDB):
    pass


class CaseWithTaskInfo(CaseDB):
    task: Task

    @staticmethod
    def get_case_with_task_info(case: models.CaseModel) -> Optional["CaseWithTaskInfo"]:
        task_dict = {"task_id": None, "status": None, "result": None, "error": None}

        if case.task_id:
            task = tasks.celery_app.AsyncResult(case.task_id)
            task_dict = {
                "task_id": task.id,
                "status": task.status,
                "result": task.result,
                "error": task.traceback.strip().split("\n")[-1]
                if task.traceback
                else None,
            }
        return CaseWithTaskInfo(**CaseDB.from_orm(case).dict(), task=task_dict)
