# ProfeshGPT Backend

## Setting up a Development Environment

```bash
uv sync
source .venv/bin/activate
```

```bash
cd .docker/
docker compose up
```

```bash
uvicorn src.main:app --reload --port 8000
```

```bash
celery -A src.workers.main.celery_app worker --loglevel=info
```

```bash
celery -A src.workers.main.celery_app flower --port=8300
```
