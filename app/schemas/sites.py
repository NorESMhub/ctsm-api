from pydantic import BaseModel


class SiteSchema(BaseModel):
    name: str
    compset: str
    res: str
    lat: float
    lon: float
    url: str
