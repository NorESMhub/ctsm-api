from enum import Enum

from pydantic import BaseModel


class Driver(str, Enum):
    noupc = "noupc"
    mct = "mct"


class CaseSchemaBase(BaseModel):
    id: int
    name: str
    compset: str
    res: str
    driver: Driver = Driver.noupc


class CaseSchema(CaseSchemaBase):
    pass


class CaseSchemaCreate(CaseSchema):
    pass


class CaseSchemaUpdate(CaseSchema):
    pass


class CaseSchemaDB(CaseSchemaBase):
    class Config:
        orm_mode = True
