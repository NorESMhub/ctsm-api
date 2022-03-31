from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas, tasks
from app.crud.base import CRUDBase


class CRUDCase(CRUDBase[models.CaseModel, schemas.CaseCreateDB, schemas.CaseUpdate]):
    def get_case_with_task_info(
        self, db: Session, *, case_id: str
    ) -> Optional[schemas.CaseWithTaskInfo]:
        task_dict = {"task_id": None, "status": None, "result": None, "error": None}
        case = self.get(db, id=case_id)
        if not case:
            return None

        if case.task_id:
            task = tasks.celery_app.AsyncResult(case.task_id)
            task_dict = {
                "task_id": task.id,
                "status": task.status,
                "result": task.result,
                "error": task.traceback.strip().split("\n")[-1]
                if task.traceback
                else None,
            }
        return schemas.CaseWithTaskInfo(
            **schemas.CaseDB.from_orm(case).dict(), task=task_dict
        )


case = CRUDCase(models.CaseModel)
