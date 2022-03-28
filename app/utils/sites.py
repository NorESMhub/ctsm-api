from typing import List, Optional

from pydantic import parse_file_as

from app import schemas
from app.core import settings


def get_all_sites() -> List[schemas.Site]:
    return (
        parse_file_as(List[schemas.Site], settings.SITES_PATH)
        if settings.SITES_PATH.exists()
        else []
    )


def get_site_by_name(site_name: str) -> Optional[schemas.Site]:
    """
    Return the site info for a given site name from `resources/config/sites.json`.
    """
    site = next(filter(lambda s: s.name == site_name, get_all_sites()), None)
    return site
