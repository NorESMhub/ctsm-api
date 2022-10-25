import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Field, root_validator, validator

from app.schemas.constants import ModelDriver
from app.utils.type_casting import to_bool

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_ROOT = PROJECT_ROOT / "resources" / "model"
CASES_ROOT = PROJECT_ROOT / "resources" / "cases"
DATA_ROOT = PROJECT_ROOT / "resources" / "data"
CESMDATAROOT = (
    DATA_ROOT / "shared"
)  # if this is changed, also change in entrypoint_setup.sh and other relevant places.
CUSTOM_SITES_DATA_ROOT = DATA_ROOT / "custom_sites"
ARCHIVES_ROOT = PROJECT_ROOT / "resources" / "archives"
VARIABLES_CONFIG_PATH = PROJECT_ROOT / "resources" / "config" / "variables_config.json"

SITES_PATH = PROJECT_ROOT / "resources" / "config" / "sites.json"

CTSM_ROOT = PROJECT_ROOT / "resources" / "ctsm"
CTSM_REPO = "https://github.com/ESCOMP/CTSM.git"
CTSM_VERSION = "ctsm5.1.dev112"


for path in [ARCHIVES_ROOT, CASES_ROOT, CESMDATAROOT, CUSTOM_SITES_DATA_ROOT]:
    if not path.exists():
        path.mkdir(parents=True)


class Settings(BaseSettings):
    # API settings
    DEBUG: bool = False

    API_V1: str = Field("/api/v1", const=True)

    BACKEND_CORS_ORIGINS: List[Any] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Auth
    ALGORITHM: str = Field("HS256", const=True)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SECRET_KEY: Optional[str]

    @validator("SECRET_KEY", pre=True)
    def get_secret_key(cls, v: str, values: Dict[str, Any]) -> str:
        if not v and values.get("DEBUG"):
            return "secret"
        if not v:
            raise ValueError("SECRET_KEY must be set")
        return v

    # Database settings
    SQLALCHEMY_DATABASE_URI: str = (
        f"sqlite:///{PROJECT_ROOT / 'resources'}/cases.sqlite"
    )

    # Tasks settings
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = f"db+{str(SQLALCHEMY_DATABASE_URI)}"

    # Paths
    MODEL_ROOT: Path = Field(MODEL_ROOT, const=True)
    CASES_ROOT: Path = Field(CASES_ROOT, const=True)
    DATA_ROOT: Path = Field(DATA_ROOT, const=True)
    CUSTOM_SITES_DATA_ROOT: Path = Field(CUSTOM_SITES_DATA_ROOT, const=True)
    ARCHIVES_ROOT: Path = Field(ARCHIVES_ROOT, const=True)
    SITES_PATH: Path = Field(SITES_PATH, const=True)
    VARIABLES_CONFIG_PATH: Path = Field(VARIABLES_CONFIG_PATH, const=True)

    # Model settings
    SKIP_MODEL_CHECKS: bool = False
    MODEL_VERSION: str  # This can be a branch name, a tag, or a commit hash
    MODEL_REPO: AnyHttpUrl = CTSM_REPO  # type: ignore
    MACHINE_NAME: str = Field("docker", const=True)
    CESMDATAROOT: Path = Field(CESMDATAROOT, const=True)
    MODEL_DRIVERS: List[ModelDriver] = [ModelDriver.mct, ModelDriver.nuopc]

    # CTSM settings
    # CTSM is needed for data creation.
    # If the main model is different from CTSM, we need to clone it in a separate folder called ctsm.
    # Otherwise, we use the existing model.
    ENABLE_DATA_CREATION: bool = True
    CTSM_ROOT: Path = Field(CTSM_ROOT, const=True)
    CTSM_REPO: AnyHttpUrl = Field(CTSM_REPO, const=True)  # type: ignore
    CTSM_VERSION: str = Field(CTSM_VERSION, const=True)

    @root_validator
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if to_bool(os.environ.get("PYTHON_TEST", False)):
            values[
                "SQLALCHEMY_DATABASE_URI"
            ] = f"sqlite:///{PROJECT_ROOT / 'resources'}/cases_test.sqlite"
        if values["MODEL_REPO"].lower() == values["CTSM_REPO"].lower():
            values["CTSM_ROOT"] = values["MODEL_ROOT"]
        return values

    class Config:
        env_file = PROJECT_ROOT / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
