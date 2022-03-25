import hashlib
import json

from app.core.config import get_settings
from app.schemas import CaseDB

settings = get_settings()


def get_case_id(case: CaseDB) -> str:
    """
    Case id is a hash of the compset, res, variables, data_url, driver, and ctsm_tag.
    This value is also used as the case path under `resources/cases/`.
    """
    hash_parts = "_".join(
        [
            case.compset,
            case.res,
            json.dumps(sorted(case.variables.items())),
            case.data_url,
            case.driver,
            case.ctsm_tag,
        ]
    )
    case_id = bytes(hash_parts.encode("utf-8"))
    return hashlib.md5(case_id).hexdigest()
