from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import get_settings
from app.crud.base import CRUDBase
from app.tasks import celery_app

settings = get_settings()


class CRUDCase(CRUDBase[models.CaseModel, schemas.CaseCreateDB, schemas.CaseUpdate]):
    def get_case_with_task_info(
        self, db: Session, *, case_id: str
    ) -> Optional[schemas.CaseWithTaskInfo]:
        task_dict = {"task_id": None, "status": None, "result": None, "error": None}
        case = self.get(db, id=case_id)
        if not case:
            return None

        if case.task_id:
            task = celery_app.AsyncResult(case.task_id)
            task_dict = {
                "task_id": task.id,
                "status": task.status,
                "result": task.result,
                "error": task.traceback.strip().split("\n")[-1]
                if task.traceback
                else None,
            }
        return schemas.CaseWithTaskInfo(**task_dict, case=case)


crud_case = CRUDCase(models.CaseModel)
