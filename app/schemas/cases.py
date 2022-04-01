from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, parse_file_as, validator

from app.core import settings
from app.utils.logger import logger

from .tasks import Task


class CTSMDriver(str, Enum):
    """The driver to use with CTSM create_newcase script."""

    nuopc = "nuopc"
    mct = "mct"


class CTSMVarType(str, Enum):
    char = "char"
    integer = "integer"
    logical = "logical"
    date = "date"


class CaseStatus(str, Enum):
    INITIALISED = "INITIALISED"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SETUP = "SETUP"
    BUILT = "BUILT"
    SUBMITTED = "SUBMITTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CaseBase(BaseModel):
    compset: str
    res: str
    variables: Dict[str, Any] = {}
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

    @validator("variables", pre=True, always=True)
    def validate_variables(cls, variables: Dict[str, Any]) -> Dict[str, Any]:
        allowed_variables = get_case_allowed_variables()
        filtered_variables = {}
        errors = []
        for key, value in variables.items():
            var_props = next(filter(lambda v: v.name == key, allowed_variables), None)
            if not var_props:
                errors.append(f"Variable {key} is not allowed.")
                continue

            validated_value: Optional[Union[str, int, bool]] = None

            if var_props.type == "char":
                try:
                    validated_value = str(value)
                except Exception as e:
                    # This should never happen.
                    logger.error(f"Failed to convert variable {key} to string: {e}")
                    errors.append(f"Variable {key} is not valid string.")
                    continue
            elif var_props.type == "integer":
                try:
                    validated_value = int(value)
                except ValueError:
                    errors.append(f"Variable {key} is not valid integer")
                    continue
            elif var_props.type == "logical":
                try:
                    validated_value = bool(value)
                except ValueError:
                    errors.append(f"Variable {key} is not valid boolean")

            if var_props.choices and value not in var_props.choices:
                errors.append(f"{value} is not a valid choice for {key}.")
                continue

            if not validated_value:
                errors.append(f"Variable {key} is not valid.")
                continue

            filtered_variables[key] = validated_value

        if errors:
            raise ValueError(errors)

        return filtered_variables


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


class CaseAllowedVariable(BaseModel):
    name: str
    # The type values are based on what is used in CTSM xml files, except for date,
    # which is char in yyyy-mm-dd format in CTSM.
    type: CTSMVarType
    choices: Optional[List[Union[str, int]]] = None
    description: Optional[str] = None
    default: Optional[Union[str, int, bool]] = None


def get_case_allowed_variables() -> List[CaseAllowedVariable]:
    return (
        parse_file_as(List[CaseAllowedVariable], settings.CASE_ALLOWED_VARS_PATH)
        if settings.CASE_ALLOWED_VARS_PATH.exists()
        else []
    )
