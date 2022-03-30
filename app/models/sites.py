from sqlalchemy import Column, ForeignKey, Integer, String

from app.db.base_class import Base


class SiteCaseModel(Base):
    __tablename__ = "case_sites"

    id: int = Column(Integer(), primary_key=True, index=True)
    name: str = Column(String(300), nullable=False)
    case_id: str = Column(
        String(32), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    date_created: str = Column(String(30), nullable=False)
