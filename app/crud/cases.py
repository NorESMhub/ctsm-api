from app.core.config import get_settings
from app.crud.base import CRUDBase
from app.models import CaseModel
from app.schemas import CaseSchemaCreateDB, CaseSchemaUpdate

settings = get_settings()


class CRUDCase(CRUDBase[CaseModel, CaseSchemaCreateDB, CaseSchemaUpdate]):
    pass


crud_case = CRUDCase(CaseModel)
