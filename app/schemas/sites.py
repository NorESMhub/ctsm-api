from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SiteProperties(BaseModel):
    name: str
    description: Optional[str]
    compset: str
    res: str
    url: str


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
