from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .cases import CaseVariable, CTSMDriver


class SiteProperties(BaseModel):
    name: str
    description: Optional[str]
    compset: str
    data_url: str
    # List of site specific variables that cannot be edited by the user.
    # These are readonly variables in `variables_config.json` and are set from the site properties.
    # These are mainly path variables in the site data folder, fetched from the `data_url` property.
    config: Optional[List[CaseVariable]]


class SiteCaseCreate(BaseModel):
    site_name: str
    case_name: Optional[str]
    variables: List[CaseVariable] = []
    driver: CTSMDriver = CTSMDriver.mct

    class Config:
        schema_extra = {
            "example": {
                "site_name": "ALP1",
                "variables": [
                    {"name": "STOP_OPTION", "value": "nmonths"},
                    {"name": "STOP_N", "value": 3},
                ],
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
