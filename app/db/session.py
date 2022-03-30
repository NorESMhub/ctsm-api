from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        db.execute(text("PRAGMA foreign_keys=ON"))
        yield db
    finally:
        db.close()
