import hashlib
from typing import Optional

from app.core.config import SITES, get_settings
from app.schemas import SiteSchema

settings = get_settings()


def get_site_id(compset: str, res: str, driver: str, data_url: str) -> str:
    """
    Site id is a hash of the compset, res, driver, and data_url.
    This value is also used as the case path under `resources/cases/`.
    """
    case_path = bytes(
        f"{compset}_{res}_{driver}_{data_url}_{settings.CTSM_TAG}".encode("utf-8")
    )
    return hashlib.md5(case_path).hexdigest()


def get_site_by_name(site_name: str) -> Optional[SiteSchema]:
    """
    Return the site info for a given site name from `resources/config/sites.json`.
    """
    site = next(filter(lambda s: s.name == site_name, SITES), None)
    return site
