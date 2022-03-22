from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .tasks import TaskSchema


class CTSMDriver(str, Enum):
    """The driver to use with CTSM create_newcase script."""

    nuopc = "nuopc"
    mct = "mct"


class CaseStatus(str, Enum):
    initialised = "initialised"
    created = "created"
    setup = "setup"
    built = "built"
    submitted = "submitted"
    succeeded = "succeeded"
    failed = "failed"


class CaseSchemaBase(BaseModel):
    name: str
    compset: str
    res: str
    driver: CTSMDriver = CTSMDriver.mct
    data_url: str

    class Config:
        schema_extra = {
            "example": {
                "name": "ALP1",
                "compset": "2000_DATM%1PTGSWP3_CLM50%FATES_SICE_SOCN_MOSART_SGLC_SWAV",
                "res": "1x1_ALP1",
                "driver": "nuopc",
                "data_url": "https://ns2806k.webs.sigma2.no/EMERALD/EMERALD_platform/inputdata_fates_platform/inputdata_version2.0.0_ALP1.tar",  # noqa: E501
            }
        }


class CaseSchemaCreate(CaseSchemaBase):
    pass


class CaseSchemaDBBase(CaseSchemaBase):
    ctsm_tag: str
    status: CaseStatus = CaseStatus.initialised
    date_created: datetime = datetime.now()
    task_id: Optional[str] = None

    class Config:
        orm_mode = True


class CaseSchema(CaseSchemaDBBase):
    id: str


class CaseSchemaCreateDB(CaseSchema):
    pass


class CaseSchemaUpdate(CaseSchema):
    pass


class CaseSchemaWithTaskInfo(TaskSchema):
    case: CaseSchema
