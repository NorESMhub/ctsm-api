from typing import Optional

from app.core.config import SITES, get_settings
from app.schemas import SiteSchema

settings = get_settings()


def get_site_by_name(site_name: str) -> Optional[SiteSchema]:
    """
    Return the site info for a given site name from `resources/config/sites.json`.
    """
    site = next(filter(lambda s: s.name == site_name, SITES), None)
    return site
