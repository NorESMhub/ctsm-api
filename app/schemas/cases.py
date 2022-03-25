from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel

from .tasks import Task


class CTSMDriver(str, Enum):
    """The driver to use with CTSM create_newcase script."""

    nuopc = "nuopc"
    mct = "mct"


class CaseStatus(str, Enum):
    initialised = "initialised"
    created = "created"
    updated = "updated"
    setup = "setup"
    built = "built"
    submitted = "submitted"
    succeeded = "succeeded"
    failed = "failed"


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
                "driver": "mct",
                "data_url": "https://ns2806k.webs.sigma2.no/EMERALD/EMERALD_platform/inputdata_fates_platform/inputdata_version2.0.0_ALP1.tar",  # noqa: E501
            }
        }


class CaseDB(CaseBase):
    id: str
    ctsm_tag: str
    status: CaseStatus = CaseStatus.initialised
    date_created: datetime = datetime.now()
    task_id: Optional[str] = None

    class Config:
        orm_mode = True


class CaseCreateDB(CaseDB):
    pass


class CaseUpdate(CaseDB):
    pass


class CaseWithTaskInfo(Task):
    case: CaseDB
