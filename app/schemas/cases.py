from enum import Enum

from pydantic import BaseModel


class Driver(str, Enum):
    noupc = "noupc"
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
    id: int
    name: str
    compset: str
    res: str
    driver: Driver = Driver.noupc
    ctsm_tag: str
    status: Status = Status.initialised


class CaseSchema(CaseSchemaBase):
    pass


class CaseSchemaCreate(CaseSchema):
    pass


class CaseSchemaUpdate(CaseSchema):
    pass


class CaseSchemaDB(CaseSchemaBase):
    class Config:
        orm_mode = True
