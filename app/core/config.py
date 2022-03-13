import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from pydantic import AnyHttpUrl, BaseSettings, validator

from app.utils.type_casting import to_bool

PROJECT_ROOT = Path(__file__).parent.parent.parent
CTSM_ROOT = PROJECT_ROOT / "resources" / "ctsm"
CASES_ROOT = PROJECT_ROOT / "resources" / "cases"
DATA_ROOT = PROJECT_ROOT / "resources" / "data"
API_V1 = "/api/v1"

if not CASES_ROOT.exists():
    CASES_ROOT.mkdir(parents=True)


class Settings(BaseSettings):
    DEBUG: bool = False

    CTSM_TAG: str
    CTSM_REPO: AnyHttpUrl = "https://github.com/ESCOMP/CTSM/"  # type: ignore
    DATA_ROOT: Path = os.environ.setdefault("CESMDATAROOT", str(DATA_ROOT.resolve()))

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
