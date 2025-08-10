import asyncio
from uuid import UUID

from src.common.logger import logger
from src.database.postgres.postgres_client import postgres_client
from src.database.redis.redis_client import redis_client
from src.modules.agent.core.ai_agent import AIAgent
from src.modules.agent.repositories.agent_repository import AgentRepository
from src.modules.agent.repositories.agent_status_repository import (
    AgentStatusRepository,
)
from src.modules.agent.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentProcessingCompleteEvent,
    AgentProcessingErrorEvent,
    AgentProcessingProgressEvent,
    AgentProcessingStartEvent,
    AgentStatus,
)
from src.modules.agent.services.agent_crud_service import AgentCRUDService
from src.modules.agent.services.agent_service import AgentService
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.workers.main import celery_app


@celery_app.task
def run_agent_task(input_text: str):
    try:
        run_id = run_agent_task.request.id
        logger.info(f"Starting agent task for run_id: {run_id}")

        ai_agent = AIAgent()
        repository = AgentStatusRepository(redis_client=redis_client)
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


@celery_app.task
def process_agent_creation_task(request_data: dict, user_id: str):
    try:
        task_id = process_agent_creation_task.request.id
        logger.info(
            f"Starting agent creation processing for user_id: {user_id}, task_id: {task_id}"
        )

        db = next(postgres_client.get_db())
        agent_repository = AgentRepository(db)
        resume_repository = ResumeRepository(db)
        status_repository = AgentStatusRepository(redis_client=redis_client)

        service = AgentCRUDService(agent_repository, resume_repository)
        request = AgentCreateRequest(**request_data)
        agent = service.create_agent(request, user_id)

        service.update_agent_task_id(agent.agent_id, user_id, task_id)

        asyncio.run(
            _process_agent_creation(
                agent_id=str(agent.agent_id),
                resume_id=str(agent.curr_resume_id),
                task_id=task_id,
                service=service,
                status_repository=status_repository,
            )
        )

        logger.info(
            f"Completed agent creation processing for agent_id: {agent.agent_id}"
        )
        return {
            "status": "completed",
            "agent_id": str(agent.agent_id),
            "task_id": task_id,
        }

    except Exception as e:
        task_id = getattr(process_agent_creation_task.request, "id", "unknown")
        logger.error(
            f"Agent creation processing failed for user_id {user_id}, task_id {task_id}: {e}"
        )

        try:
            db = next(postgres_client.get_db())
            agent_repository = AgentRepository(db)
            status_repository = AgentStatusRepository(redis_client=redis_client)
            service = AgentCRUDService(agent_repository, None)

            if "agent" in locals():
                asyncio.run(
                    _handle_processing_error(
                        agent_id=str(agent.agent_id),
                        task_id=task_id,
                        error_message=str(e),
                        service=service,
                        status_repository=status_repository,
                    )
                )
        except Exception as cleanup_error:
            logger.error(f"Failed to handle processing error: {cleanup_error}")

        return {
            "status": "failed",
            "user_id": user_id,
            "task_id": task_id,
            "error": str(e),
        }


async def _process_agent_creation(
    agent_id: str,
    resume_id: str,
    task_id: str,
    service: AgentCRUDService,
    status_repository: AgentStatusRepository,
):
    try:
        agent_uuid = UUID(agent_id)
        resume_uuid = UUID(resume_id)

        start_event = AgentProcessingStartEvent(
            run_id=task_id,
            agent_id=agent_id,
            task_id=task_id,
            message="Starting agent processing",
        )
        await status_repository.publish_event(task_id, start_event)

        service.update_agent_status(agent_uuid, AgentStatus.IN_PROGRESS)

        progress_event = AgentProcessingProgressEvent(
            run_id=task_id,
            agent_id=agent_id,
            progress="Validating resume",
            status=AgentStatus.IN_PROGRESS,
            message="Validating resume document",
        )
        await status_repository.publish_event(task_id, progress_event)
        await asyncio.sleep(2)

        resume = service.get_resume_by_id(resume_uuid)
        if not resume:
            raise ValueError("Resume not found")

        progress_event = AgentProcessingProgressEvent(
            run_id=task_id,
            agent_id=agent_id,
            progress="Processing resume content",
            status=AgentStatus.IN_PROGRESS,
            message="Processing resume content for embedding",
        )
        await status_repository.publish_event(task_id, progress_event)
        await asyncio.sleep(3)

        progress_event = AgentProcessingProgressEvent(
            run_id=task_id,
            agent_id=agent_id,
            progress="Generating embeddings",
            status=AgentStatus.IN_PROGRESS,
            message="Generating embeddings for resume content",
        )
        await status_repository.publish_event(task_id, progress_event)
        await asyncio.sleep(4)

        progress_event = AgentProcessingProgressEvent(
            run_id=task_id,
            agent_id=agent_id,
            progress="Finalizing agent setup",
            status=AgentStatus.IN_PROGRESS,
            message="Finalizing agent configuration",
        )
        await status_repository.publish_event(task_id, progress_event)
        await asyncio.sleep(2)

        service.update_agent_status(agent_uuid, AgentStatus.COMPLETED)

        complete_event = AgentProcessingCompleteEvent(
            run_id=task_id,
            agent_id=agent_id,
            status=AgentStatus.COMPLETED,
            message="Agent processing completed successfully",
        )
        await status_repository.publish_event(task_id, complete_event)

    except Exception as e:
        logger.error(f"Error in agent creation processing: {e}")
        await _handle_processing_error(
            agent_id=agent_id,
            task_id=task_id,
            error_message=str(e),
            service=service,
            status_repository=status_repository,
        )
        raise


async def _handle_processing_error(
    agent_id: str,
    task_id: str,
    error_message: str,
    service: AgentCRUDService,
    status_repository: AgentStatusRepository,
):
    try:
        agent_uuid = UUID(agent_id)
        service.update_agent_status(agent_uuid, AgentStatus.FAILED)

        error_event = AgentProcessingErrorEvent(
            run_id=task_id,
            agent_id=agent_id,
            error_message=error_message,
            status=AgentStatus.FAILED,
            message="Agent processing failed",
        )
        await status_repository.publish_event(task_id, error_event)

    except Exception as e:
        logger.error(f"Failed to handle processing error: {e}")
        raise
