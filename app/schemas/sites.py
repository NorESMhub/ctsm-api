from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .cases import CaseAllowedVariable, CTSMDriver


class SiteProperties(BaseModel):
    name: str
    description: Optional[str]
    compset: str
    res: str
    url: str


class SiteCaseCreate(BaseModel):
    site_name: str
    variables: List[CaseAllowedVariable] = []
    driver: CTSMDriver = CTSMDriver.mct

    class Config:
        schema_extra = {
            "example": {
                "site_name": "ALP1",
                "variables": {"STOP_OPTION": "nmonths", "STOP_N": 3},
                "driver": CTSMDriver.mct,
            }
        }


class SiteCaseDBBase(BaseModel):
    name: str
    case_id: str
    date_created: datetime = datetime.now()

    class Config:
        orm_mode = True


class SiteCaseDB(SiteCaseDBBase):
    id: int


class SiteCaseDBCreate(SiteCaseDBBase):
    pass


class SiteCaseDBUpdate(SiteCaseDB):
    pass
