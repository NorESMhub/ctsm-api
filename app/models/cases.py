from sqlalchemy import Column, Integer, String

from app.db.base_class import Base


class CaseModel(Base):
    __tablename__ = "cases"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(300), nullable=False, index=True)
    compset: str = Column(String(300), nullable=False, index=True)
    res: str = Column(String(100), nullable=False, index=True)
    driver: str = Column(String(5), nullable=False, index=True)
