import hashlib

from app.core.config import get_settings

settings = get_settings()


def get_case_id(compset: str, res: str, driver: str, data_url: str) -> str:
    """
    Case id is a hash of the compset, res, driver, and data_url.
    This value is also used as the case path under `resources/cases/`.
    """
    case_path = bytes(
        f"{compset}_{res}_{driver}_{data_url}_{settings.CTSM_TAG}".encode("utf-8")
    )
    return hashlib.md5(case_path).hexdigest()
