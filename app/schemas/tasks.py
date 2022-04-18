from enum import Enum
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
    RETRY = "RETRY"
    IGNORED = "IGNORED"


class Task(BaseModel):
    task_id: Optional[str]
    status: Optional[TaskStatus]
    result: Optional[Any]
    error: Optional[str]
