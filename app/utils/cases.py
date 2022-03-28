import hashlib
import json
from pathlib import Path

from app import schemas
from app.core import settings


def get_case_id(case: schemas.CaseDB) -> str:
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


def get_case_data_path(data_url: str) -> Path:
    return settings.DATA_ROOT / hashlib.md5(bytes(data_url.encode("utf-8"))).hexdigest()
