from celery import Celery

from src.common.config import settings
from src.common.logger import logger, setup_logging


def create_celery_app():
    setup_logging()

    logger.info(f"REDIS_URL: {settings.REDIS_URL}")

    celery_app = Celery(
        "lorem-ipsum-api",
        broker=settings.REDIS_URL,
        include=["src.workers.tasks.test"],
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )

    celery_app.conf.worker_hijack_root_logger = False

    return celery_app


celery_app = create_celery_app()
