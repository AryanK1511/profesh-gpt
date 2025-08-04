from src.workers.main import celery_app


@celery_app.task
def test_task():
    return "Hello, world!"
