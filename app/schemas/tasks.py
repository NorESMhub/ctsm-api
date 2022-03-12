from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class Status(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
    RETRY = "RETRY"
    IGNORED = "IGNORED"


class TaskSchema(BaseModel):
    task_id: str
    status: Status
    result: Any


def get_item_with_task_info(schema_type: Generic[SchemaType]):
    class ItemWithTaskInfoSchema(TaskSchema):
        item: SchemaType

    return ItemWithTaskInfoSchema
