import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Union

from pydantic import AnyHttpUrl, BaseSettings, Field, validator

from app.utils.type_casting import to_bool

PROJECT_ROOT = Path(__file__).parent.parent.parent
CTSM_ROOT = PROJECT_ROOT / "resources" / "ctsm"
CASES_ROOT = PROJECT_ROOT / "resources" / "cases"
DATA_ROOT = PROJECT_ROOT / "resources" / "data"
ARCHIVES_ROOT = PROJECT_ROOT / "resources" / "archives"
VARIABLES_CONFIG_PATH = PROJECT_ROOT / "resources" / "config" / "variables_config.json"

SITES_PATH = PROJECT_ROOT / "resources" / "config" / "sites.json"


for path in [CASES_ROOT, ARCHIVES_ROOT]:
    if not path.exists():
        path.mkdir(parents=True)


class Settings(BaseSettings):
    # API settings
    DEBUG: bool = False

    API_V1: str = Field("/api/v1", const=True)

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    SQLALCHEMY_DATABASE_URI: str = (
        f"sqlite:///{PROJECT_ROOT / 'resources'}/cases.sqlite"
    )

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def get_db_uri(cls, v: str, values: Dict[str, Any]) -> Any:
        return (
            f"sqlite:///{PROJECT_ROOT / 'resources'}/cases_test.sqlite"
            if to_bool(os.environ.get("PYTHON_TEST", False))
            else v
        )

    # Tasks settings
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = f"db+{str(SQLALCHEMY_DATABASE_URI)}"

    # Paths
    CTSM_ROOT: Path = Field(CTSM_ROOT, const=True)
    CASES_ROOT: Path = Field(CASES_ROOT, const=True)
    DATA_ROOT: Path = Field(DATA_ROOT, const=True)
    ARCHIVES_ROOT: Path = Field(ARCHIVES_ROOT, const=True)
    SITES_PATH: Path = Field(SITES_PATH, const=True)
    VARIABLES_CONFIG_PATH: Path = Field(VARIABLES_CONFIG_PATH, const=True)

    # CTSM settings
    SKIP_CTSM_CHECKS: bool = False
    CTSM_TAG: str
    CTSM_REPO: AnyHttpUrl = "https://github.com/ESCOMP/CTSM/"  # type: ignore
    MACHINE_NAME: str = "container"

    class Config:
        env_file = PROJECT_ROOT / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
