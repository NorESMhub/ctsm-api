from sqlalchemy import Column, String

from app.db.base_class import Base


class CaseModel(Base):
    __tablename__ = "cases"

    # Id is calculated from the case compset, res, and driver,
    # and used as the case path.
    id: str = Column(String(32), primary_key=True, index=True)
    name: str = Column(String(300), nullable=False)
    compset: str = Column(String(300), nullable=False)
    res: str = Column(String(100), nullable=False)
    driver: str = Column(String(5), nullable=False)
    ctsm_tag: str = Column(String(20), nullable=False)
    status: str = Column(String(20), nullable=False)
    date_created: str = Column(String(30), nullable=False)
    task_id: str = Column(String(20), nullable=True)
