from typing import List

from sqlalchemy.orm import Session

from app import models, schemas
from app.crud.base import CRUDBase

from .cases import case as crud_case


class CRUDSite(
    CRUDBase[models.SiteCaseModel, schemas.SiteCaseDBCreate, schemas.SiteCaseDBUpdate]
):
    def get_site_cases(
        self, db: Session, *, site_name: str
    ) -> List[schemas.CaseWithTaskInfo]:
        site_cases = db.query(self.model).filter_by(name=site_name)
        site_cases_with_task_info = []
        for site_case in site_cases:
            case_and_site = crud_case.get_case_with_site(db, id=site_case.case_id)
            if case_and_site:
                (case, _) = case_and_site
                site_case_with_task_info = (
                    schemas.CaseWithTaskInfo.get_case_with_task_info(case, site_name)
                )
                if site_case_with_task_info:
                    site_cases_with_task_info.append(site_case_with_task_info)
        return site_cases_with_task_info


site = CRUDSite(models.SiteCaseModel)
