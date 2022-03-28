from typing import List

from sqlalchemy.orm import Session

from app import models, schemas
from app.crud.base import CRUDBase

from .cases import case


class CRUDSite(
    CRUDBase[models.SiteCaseModel, schemas.SiteCaseDBCreate, schemas.SiteCaseDBUpdate]
):
    def get_site_cases(
        self, db: Session, *, site_name: str
    ) -> List[schemas.CaseWithTaskInfo]:
        site_cases = db.query(self.model).filter_by(name=site_name)
        site_cases_with_task_info = []
        for site_case in site_cases:
            site_case_with_task_info = case.get_case_with_task_info(
                db, case_id=site_case.case_id
            )
            if site_case_with_task_info:
                site_cases_with_task_info.append(site_case_with_task_info)
        return site_cases_with_task_info


site = CRUDSite(models.SiteCaseModel)
