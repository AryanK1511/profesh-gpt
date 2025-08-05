import asyncio

from src.common.logger import logger
from src.database.redis import RedisManager
from src.modules.agent.core.ai_agent import AIAgent
from src.modules.agent.respositories.agent_status_repository import (
    AgentStatusRepository,
)
from src.modules.agent.services.agent_service import AgentService
from src.workers.main import celery_app


@celery_app.task
def run_agent_task(input_text: str):
    try:
        run_id = run_agent_task.request.id
        logger.info(f"Starting agent task for run_id: {run_id}")

        ai_agent = AIAgent()
        repository = AgentStatusRepository(redis_manager=RedisManager())
        service = AgentService(ai_agent=ai_agent, repository=repository)

        asyncio.run(
            service.run_agent_with_publishing(run_id=run_id, input_text=input_text)
        )

        logger.info(f"Completed agent task for run_id: {run_id}")
        return {"status": "completed", "run_id": run_id}

    except Exception as e:
        run_id = getattr(run_agent_task.request, "id", "unknown")
        logger.error(f"Agent task failed for run_id {run_id}: {e}")
        return {"status": "failed", "run_id": run_id, "error": str(e)}
