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
    driver: CTSMDriver = CTSMDriver.nuopc

    class Config:
        schema_extra = {
            "example": {
                "name": "example_case",
                "compset": "I2000Clm50Sp",
                "res": "f19_g17",
                "driver": "nuopc",
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
