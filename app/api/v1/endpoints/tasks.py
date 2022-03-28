from typing import Any

from fastapi import APIRouter

from app import schemas, tasks

router = APIRouter()


@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: str) -> Any:
    """
    Get the status of a task.
    """
    task = tasks.celery_app.AsyncResult(task_id)
    return schemas.Task(task_id=task.task_id, status=task.status, result=task.result)
