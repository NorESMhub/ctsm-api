import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Union

from pydantic import AnyHttpUrl, BaseSettings, parse_file_as, validator

from app.schemas import SiteSchema
from app.utils.type_casting import to_bool

PROJECT_ROOT = Path(__file__).parent.parent.parent
CTSM_ROOT = PROJECT_ROOT / "resources" / "ctsm"
CASES_ROOT = PROJECT_ROOT / "resources" / "cases"
DATA_ROOT = PROJECT_ROOT / "resources" / "data"
SITES_PATH = PROJECT_ROOT / "resources" / "config" / "sites.json"
API_V1 = "/api/v1"

if SITES_PATH.exists():
    SITES = parse_file_as(List[SiteSchema], SITES_PATH)
else:
    SITES = []

if not CASES_ROOT.exists():
    CASES_ROOT.mkdir(parents=True)


class Settings(BaseSettings):
    DEBUG: bool = False

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    CTSM_TAG: str
    CTSM_REPO: AnyHttpUrl = "https://github.com/ESCOMP/CTSM/"  # type: ignore
    MACHINE_NAME: str = "container"

    SQLITE_DB_TEST: str = "cases_test.sqlite"
    SQLITE_DB: str = "cases.sqlite"

    @validator("SQLITE_DB", pre=True)
    def get_db_name(cls, v: str, values: Dict[str, Any]) -> Any:
        return (
            values["SQLITE_DB_TEST"]
            if to_bool(os.environ.get("PYTHON_TEST", False))
            else v
        )

    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{SQLITE_DB}"

    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = f"db+{SQLALCHEMY_DATABASE_URI}"

    class Config:
        env_file = PROJECT_ROOT / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
