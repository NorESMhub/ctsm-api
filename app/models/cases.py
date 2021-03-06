from typing import Dict, List, Optional, TypedDict

from sqlalchemy import JSON, Column, String

from app.db.base_class import Base
from app.schemas.constants import VariableValue


class CaseVariable(TypedDict):
    name: str
    value: VariableValue


class CaseModel(Base):
    __tablename__ = "cases"

    # id is calculated from the case compset, res, variables,
    # data_url, driver, and ctsm_tag and used as the case path.
    id: str = Column(String(32), primary_key=True, index=True)
    name: str = Column(String(300), nullable=True)
    compset: str = Column(String(300), nullable=False)
    res: str = Column(String(100), nullable=False)
    variables: List[CaseVariable] = Column(JSON(), nullable=False)
    fates_indices: Optional[str] = Column(String(300), nullable=True)
    data_url: str = Column(String(300), nullable=False)
    driver: str = Column(String(5), nullable=False)
    ctsm_tag: str = Column(String(20), nullable=False)
    env: Dict[str, str] = Column(JSON(), nullable=False, default={})
    status: str = Column(String(20), nullable=False)
    date_created: str = Column(String(30), nullable=False)
    create_task_id: Optional[str] = Column(String(20), nullable=True)
    run_task_id: Optional[str] = Column(String(20), nullable=True)
