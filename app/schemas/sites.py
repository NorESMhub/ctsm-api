from datetime import datetime

from pydantic import BaseModel


class Site(BaseModel):
    name: str
    compset: str
    res: str
    lat: float
    lon: float
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
