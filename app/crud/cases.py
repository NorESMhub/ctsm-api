import hashlib

from app.core.config import get_settings
from app.crud.base import CRUDBase
from app.models import CaseModel
from app.schemas import CaseSchemaCreateDB, CaseSchemaUpdate

settings = get_settings()


class CRUDCase(CRUDBase[CaseModel, CaseSchemaCreateDB, CaseSchemaUpdate]):
    @staticmethod
    def get_case_path(compset: str, res: str, driver: str) -> str:
        case_path = bytes(
            f"{compset}_{res}_{driver}_{settings.CTSM_TAG}".encode("utf-8")
        )
        return hashlib.md5(case_path).hexdigest()


crud_case = CRUDCase(CaseModel)
