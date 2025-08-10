import asyncio
from uuid import UUID

from src.common.logger import logger
from src.modules.agent.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentProcessingCompleteEvent,
    AgentProcessingErrorEvent,
    AgentProcessingStartEvent,
    AgentStatus,
)
from src.workers.dependencies import (
    create_agent_processing_service,
    create_agent_service,
    create_agent_status_repository,
)
from src.workers.main import celery_app


@celery_app.task
def run_agent_task(input_text: str):
    try:
        run_id = run_agent_task.request.id
        logger.info(f"Starting agent task for run_id: {run_id}")

        service = create_agent_processing_service()

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

        service = create_agent_service()
        status_repository = create_agent_status_repository()
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
            service = create_agent_service()
            status_repository = create_agent_status_repository()

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
    service,
    status_repository,
):
    try:
        agent_uuid = UUID(agent_id)

        start_event = AgentProcessingStartEvent(
            run_id=task_id,
            task_id=task_id,
            agent_id=agent_id,
            message="Starting agent processing",
        )
        await status_repository.publish_event(task_id, start_event)

        # Wait 30 seconds
        await asyncio.sleep(30)

        # Update status to IN_PROGRESS
        service.update_agent_status(agent_uuid, AgentStatus.IN_PROGRESS)

        # Wait another 30 seconds
        await asyncio.sleep(30)

        service.update_agent_status(agent_uuid, AgentStatus.COMPLETED)

        complete_event = AgentProcessingCompleteEvent(
            run_id=task_id,
            agent_id=agent_id,
            status=AgentStatus.COMPLETED,
            message="Agent processing completed successfully",
        )
        await status_repository.publish_event(task_id, complete_event)

        logger.info(f"Successfully completed agent processing for agent_id: {agent_id}")

    except Exception as e:
        logger.error(f"Error during agent processing for agent_id {agent_id}: {e}")
        service.update_agent_status(agent_uuid, AgentStatus.FAILED)

        error_event = AgentProcessingErrorEvent(
            run_id=task_id,
            agent_id=agent_id,
            error_message=str(e),
            status=AgentStatus.FAILED,
            message="Agent processing failed",
        )
        await status_repository.publish_event(task_id, error_event)
        raise


async def _handle_processing_error(
    agent_id: str,
    task_id: str,
    error_message: str,
    service,
    status_repository,
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

        logger.info(f"Handled processing error for agent_id: {agent_id}")

    except Exception as e:
        logger.error(f"Failed to handle processing error for agent_id {agent_id}: {e}")
        raise
