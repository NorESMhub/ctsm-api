from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "tasks", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
)


class CeleryConfig:
    """
    Change the default serializer to allow passing of db models
    and pydantic schemas to celery tasks.
    """

    task_serializer = "pickle"
    result_serializer = "pickle"
    event_serializer = "json"
    accept_content = ["application/json", "application/x-python-serialize"]
    result_accept_content = ["application/json", "application/x-python-serialize"]


celery_app.config_from_object(CeleryConfig)
