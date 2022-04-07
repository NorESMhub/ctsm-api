import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, parse_file_as, validator

from app import models, tasks
from app.core import settings
from app.utils.logger import logger

from .tasks import Task


class CTSMVarType(str, Enum):
    """The type values are based on what is used in CTSM xml files,
    except for date, which is char in yyyy-mm-dd format in CTSM."""

    char = "char"
    integer = "integer"
    logical = "logical"
    date = "date"


CTSM_VAR_VALUE_TYPES = Union[str, int, bool, List[Union[str, int, bool]]]


class VariableValidation(BaseModel):
    min: Optional[Union[int, float]]
    max: Optional[Union[int, float]]
    pattern: Optional[str]
    choices: Optional[List[Union[str, int]]]


class VariableCategory(str, Enum):
    ctsm_xml = "ctsm_xml"
    ctsm_nl_ln = "ctsm_nl_lnd"
    fates = "fates"


class CaseAllowedVariable(BaseModel):
    name: str
    category: VariableCategory
    type: CTSMVarType
    description: Optional[str]
    allow_multiple: bool = False
    validation: Optional[VariableValidation]
    default: Optional[CTSM_VAR_VALUE_TYPES]
    value: Optional[CTSM_VAR_VALUE_TYPES]

    @classmethod
    def get_case_allowed_variables(cls) -> List["CaseAllowedVariable"]:
        return (
            parse_file_as(List[CaseAllowedVariable], settings.CASE_ALLOWED_VARS_PATH)
            if settings.CASE_ALLOWED_VARS_PATH.exists()
            else []
        )


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
    variables: List[CaseAllowedVariable] = []
    driver: CTSMDriver = CTSMDriver.mct
    data_url: str

    class Config:
        schema_extra = {
            "example": {
                "compset": "2000_DATM%1PTGSWP3_CLM50%FATES_SICE_SOCN_MOSART_SGLC_SWAV",
                "res": "1x1_ALP1",
                "variables": {},
                "driver": CTSMDriver.mct,
                "data_url": "https://ns2806k.webs.sigma2.no/EMERALD/EMERALD_platform/inputdata_fates_platform/inputdata_version2.0.0_ALP1.tar",  # noqa: E501
            }
        }

    @validator("variables", always=True)
    def validate_variables(
        cls, variables: List[Union[CaseAllowedVariable, Dict[str, Any]]]
    ) -> List[CaseAllowedVariable]:
        allowed_variables = CaseAllowedVariable.get_case_allowed_variables()
        validated_variables = []
        errors = None

        for variable in variables:
            if isinstance(variable, dict):
                variable = CaseAllowedVariable(**variable)

            if not variable.value:
                continue

            var_props = next(
                filter(lambda v: v.name == variable.name, allowed_variables), None
            )
            if not var_props:
                errors = f"Variable {variable.name} is not allowed."
                continue

            value = variable.value
            if var_props.allow_multiple:
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
                validated_value: Optional[Union[str, int, bool]] = None

                if var_props.type == "char":
                    try:
                        validated_value = str(v)
                    except Exception as e:
                        # This should never happen.
                        logger.error(
                            f"Failed to convert variable {variable.name} to string: {e}"
                        )
                        errors = f"Variable {variable.name} is not valid string."
                        continue
                elif var_props.type == "integer":
                    try:
                        validated_value = int(v)
                    except ValueError:
                        errors = f"Variable {variable.name} is not valid integer"
                        continue
                elif var_props.type == "logical":
                    try:
                        validated_value = bool(v)
                    except ValueError:
                        errors = f"Variable {variable.name} is not valid boolean"
                        continue

                if not validated_value:
                    errors = f"Variable {variable.name} is not valid."
                    continue

                if var_props.validation:
                    if var_props.validation.choices:
                        if validated_value not in var_props.validation.choices:
                            errors = f"{variable.value} is not a valid choice for {variable.name}."
                            continue
                    else:
                        if var_props.validation.min:
                            if (
                                type(validated_value) != int
                                or type(validated_value) != float
                                or validated_value < var_props.validation.min
                            ):
                                errors = f"{variable.value} is less than minimum value for {variable.name}."
                                continue
                        if var_props.validation.max:
                            if (
                                type(validated_value) != int
                                or type(validated_value) != float
                                or validated_value > var_props.validation.max
                            ):
                                errors = f"{variable.value} is greater than maximum value for {variable.name}."
                                continue
                        if var_props.validation.pattern:
                            if type(validated_value) != str or not re.match(
                                var_props.validation.pattern, validated_value
                            ):
                                errors = f"{variable.value} does not match pattern for {variable.name}."
                                continue

                validated_values.append(validated_value)

            var_props_dict = var_props.dict()
            var_props_dict["value"] = validated_values
            validated_variables.append(CaseAllowedVariable(**var_props_dict))

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
