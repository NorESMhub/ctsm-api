import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app import models, schemas, tasks
from app.core import settings
from app.crud.base import CRUDBase
from app.tasks.celery_app import celery_app


class CRUDCase(CRUDBase[models.CaseModel, schemas.CaseCreateDB, schemas.CaseUpdate]):
    def create(
        self, db: Session, *, obj_in: Union[schemas.CaseBase, Dict[str, Any]]
    ) -> models.CaseModel:
        data = schemas.CaseCreateDB(
            **(obj_in.dict() if isinstance(obj_in, schemas.CaseBase) else obj_in)
        )
        case_id = data.id
        existing_case = self.get(db, id=case_id)

        if existing_case:
            if existing_case.status != schemas.TaskStatus.FAILURE:
                return existing_case

            self.remove(db, id=case_id)

        new_case = super().create(db, obj_in=data)
        task = tasks.create_case.delay(new_case)
        return self.update(db, db_obj=new_case, obj_in={"create_task_id": task.id})

    def remove(self, db: Session, *, id: str) -> Optional[models.CaseModel]:  # type: ignore[override]
        existing_case = self.get(db, id=id)

        if existing_case:
            case_path = settings.CASES_ROOT / existing_case.env["CASE_FOLDER_NAME"]
            if case_path.exists():
                shutil.rmtree(case_path)

            archive_path = (
                settings.ARCHIVES_ROOT / f"{existing_case.env['CASE_FOLDER_NAME']}.zip"
            )
            if archive_path.exists():
                os.remove(archive_path)

            cesm_data_root = Path(existing_case.env["CESMDATAROOT"])
            if cesm_data_root.exists():
                shutil.rmtree(cesm_data_root)

            if existing_case.create_task_id:
                celery_app.AsyncResult(existing_case.create_task_id).forget()
            if existing_case.run_task_id:
                celery_app.AsyncResult(existing_case.run_task_id).forget()

        return super().remove(db, id=id)


case = CRUDCase(models.CaseModel)
