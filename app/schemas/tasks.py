from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from .constants import TaskStatus

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class Task(BaseModel):
    task_id: Optional[str]
    status: Optional[TaskStatus]
    result: Optional[Any]
    error: Optional[str]
