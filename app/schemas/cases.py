from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, validator

from app.core import settings
from app.utils.logger import logger

from .tasks import Task


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
        filtered_variables = {}
        for key, variables in variables.items():
            if key in settings.CASE_ALLOWED_VARS:
                filtered_variables[key] = variables
            else:
                logger.warn(f"Variable {key} is not allowed")
                continue
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
