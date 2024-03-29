from typing import Dict, List, Optional, TypedDict

from sqlalchemy import JSON, Column, Float, String

from app.db.base_class import Base
from app.schemas.constants import VariableValue


class CaseVariable(TypedDict):
    name: str
    value: VariableValue


class CaseModel(Base):
    __tablename__ = "cases"

    id: str = Column(String(32), primary_key=True, index=True)
    name: str = Column(String(300), nullable=True)
    compset: str = Column(String(300), nullable=False)
    lat: Optional[float] = Column(Float, nullable=True)
    lon: Optional[float] = Column(Float, nullable=True)
    variables: List[CaseVariable] = Column(JSON(), nullable=False)
    fates_indices: Optional[str] = Column(String(300), nullable=True)
    data_url: Optional[str] = Column(String(300), nullable=True)
    data_digest: str = Column(String(300), nullable=False)
    driver: str = Column(String(5), nullable=False)
    model_version: str = Column(String(20), nullable=False)
    env: Dict[str, str] = Column(JSON(), nullable=False, default={})
    status: str = Column(String(20), nullable=False)
    date_created: str = Column(String(30), nullable=False)
    create_task_id: Optional[str] = Column(String(20), nullable=True)
    run_task_id: Optional[str] = Column(String(20), nullable=True)
