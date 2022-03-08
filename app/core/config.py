import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseSettings, validator

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Settings is class to hold all the configuration information about the server"""

    PROJECT_NAME: str
    SERVER_NAME: str
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = secrets.token_urlsafe(32)

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # Set DEBUG = False when in Production else can be set to True.
    DEBUG: bool = False

    SQLITE_DB: str = "cases.sqlite"
    SQLITE_DB_TEST: str = "cases_test.sqlite"

    @validator("SQLITE_DB", pre=True)
    def get_db_name(cls, v: str, values: Dict[str, Any]) -> Any:
        return values.get(
            "SQLITE_DB_TEST" if os.environ.get("PYTHON_TEST") else "SQLITE_DB", ""
        )

    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{SQLITE_DB}"

    class Config:
        env_file = PROJECT_ROOT / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings(PROJECT_NAME="CTSM API", SERVER_NAME="CTSM API")
