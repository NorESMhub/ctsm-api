from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD object with default methods to Create, Read, Update, Delete (CRUD)."""

    def __init__(self, model: Type[ModelType]):
        """

        Parameters
        ----------
        model : BaseModel
                A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Get a database record by id.

        Parameters
        ----------
        db : Session
            The database session.
        id : Any
            The object id to fetch from the database.

        Returns
        -------
        Optional[ModelType]
            An instance of the SQLAlchemy for the fetched object, if it exists.
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session) -> List[ModelType]:
        """Get all records from the database.

        Parameters
        ----------
        db : Session
            The database session.

        Returns
        -------
        List[ModelType]
            A list of SQLAlchemy model instances from the query.
        """
        return db.query(self.model).all()

    def create(
        self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Create a new record in the database.

        Parameters
        ----------
        db : Session
            The database session.
        obj_in : CreateSchemaType
            A Pydantic model that its attributes are used
            to create a new record in the attributes.

        Returns
        -------
        ModelType
            An instance of the SQLAlchemy model for the newly created records.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing record in the database.

        Parameters
        ----------
        db : Session
            The database session.
        db_obj : ModelType
            The database object to update.
        obj_in : Union[UpdateSchemaType, Dict[str, Any]]
            Either a Pydantic model or a dictionary of
            new values for the database object to update from.

        Returns
        -------
        ModelType
            The updated database object.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Union[int, str]) -> Optional[ModelType]:
        """Delete the database object for the given id.

        Parameters
        ----------
        db : Session
            The database session.
        id : Any
            The object id in the database to delete.

        Returns
        -------
        Optional[ModelType]
            The deleted object, if it existed in the database.
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
            return obj
        return None
