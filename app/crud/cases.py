from app.crud.base import CRUDBase
from app.models import CaseModel
from app.schemas import CaseSchemaCreate, CaseSchemaUpdate


class CRUDCase(CRUDBase[CaseModel, CaseSchemaCreate, CaseSchemaUpdate]):
    pass


crud_case = CRUDCase(CaseModel)
