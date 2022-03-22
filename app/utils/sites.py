from typing import Optional

from app.core.config import SITES
from app.schemas import CaseSchemaBase, SiteSchema
from app.utils.logger import logger


def find_case_site(case: CaseSchemaBase) -> Optional[SiteSchema]:
    sites = list(
        filter(lambda s: case.compset in s.compset and case.res in s.res, SITES)
    )

    if len(sites) == 0:
        return None

    if len(sites) > 1:
        logger.warn(f"Multiple sites found for {case.compset} {case.res}")

    return sites[0]
