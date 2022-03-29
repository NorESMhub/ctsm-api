from typing import Optional

from pydantic import parse_file_as

from app import schemas
from app.core import settings


def get_all_sites() -> schemas.FeatureCollection[schemas.SiteProperties]:
    return (
        parse_file_as(
            schemas.FeatureCollection[schemas.SiteProperties], settings.SITES_PATH
        )
        if settings.SITES_PATH.exists()
        else schemas.FeatureCollection[schemas.SiteProperties](features=[])
    )


def get_site_by_name(site_name: str) -> Optional[schemas.SiteProperties]:
    """
    Return the site info for a given site name from `resources/config/sites.json`.
    """
    sites = get_all_sites()
    features = sites.features if sites else []
    site = next(
        filter(lambda f: f.properties and f.properties.name == site_name, features),
        None,
    )

    if site:
        return site.properties

    return None
