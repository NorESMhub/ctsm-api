import hashlib
import json
import os
import shutil
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app import models, schemas, tasks
from app.core import settings
from app.crud.base import CRUDBase


class CRUDCase(CRUDBase[models.CaseModel, schemas.CaseCreateDB, schemas.CaseUpdate]):
    @staticmethod
    def get_case_id(obj_in: schemas.CaseDB) -> str:
        """
        Case id is a hash of the compset, res, variables, data_url, driver, and ctsm_tag.
        This value is also used as the case path under `resources/cases/`.
        """
        hash_parts = "_".join(
            [
                obj_in.compset,
                obj_in.res,
                json.dumps(list(map(lambda v: v.dict(), obj_in.variables))),
                obj_in.data_url,
                obj_in.driver,
                obj_in.ctsm_tag,
            ]
        )
        case_id = bytes(hash_parts.encode("utf-8"))
        return hashlib.md5(case_id).hexdigest()

    def create(
        self, db: Session, *, obj_in: Union[schemas.CaseBase, Dict[str, Any]]
    ) -> models.CaseModel:
        data = schemas.CaseCreateDB(
            **(obj_in.dict() if isinstance(obj_in, schemas.CaseBase) else obj_in),
            id="",
            ctsm_tag=settings.CTSM_TAG,
        )
        case_id = self.get_case_id(data)
        existing_case = self.get(db, id=case_id)

        if existing_case:
            if existing_case.status != schemas.TaskStatus.FAILURE:
                return existing_case

            self.remove(db, id=case_id)

        data.id = case_id
        new_case = super().create(db, obj_in=data)
        task = tasks.create_case_task.delay(new_case)
        return self.update(db, db_obj=new_case, obj_in={"task_id": task.id})

    def remove(self, db: Session, *, id: str) -> Optional[models.CaseModel]:  # type: ignore[override]
        if (settings.CASES_ROOT / id).exists():
            shutil.rmtree(settings.CASES_ROOT / id)
        if (settings.ARCHIVES_ROOT / f"{id}.tar.gz").exists():
            os.remove(settings.ARCHIVES_ROOT / f"{id}.tar.gz")
        return super().remove(db, id=id)


case = CRUDCase(models.CaseModel)
