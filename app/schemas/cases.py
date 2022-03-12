from enum import Enum

from pydantic import BaseModel

from .tasks import get_item_with_task_info


class Driver(str, Enum):
    nuopc = "nuopc"
    mct = "mct"


class Status(str, Enum):
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
    driver: Driver = Driver.nuopc

    class Config:
        schema_extra = {
            "example": {
                "name": "example_case",
                "compset": "I2000Clm50Sp",
                "res": "f19_g17",
                "driver": "nuopc",
            }
        }


class CaseSchemaDBBase(CaseSchemaBase):
    ctsm_tag: str
    status: Status = Status.initialised

    class Config:
        orm_mode = True


class CaseSchema(CaseSchemaDBBase):
    id: str


class CaseSchemaCreate(CaseSchemaDBBase):
    pass


class CaseSchemaUpdate(CaseSchema):
    pass


CaseWithTaskInfo = get_item_with_task_info(CaseSchema)
