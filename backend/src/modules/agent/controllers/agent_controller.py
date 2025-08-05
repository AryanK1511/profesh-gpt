from fastapi import APIRouter
from src.common.logger import logger
from src.common.utils.response import Response, Status
from src.modules.agent.schemas.agent_schemas import AgentRunRequest, AgentRunResponse
from src.workers.tasks.agent_tasks import run_agent_task

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run")
async def run_agent(request: AgentRunRequest):
    try:
        task = run_agent_task.delay(request.input_text)

        logger.info(f"Queued agent task with run_id: {task.id}")

        response_data = AgentRunResponse(run_id=task.id, status="queued")

        return Response.success(
            data=response_data.model_dump(),
            status_code=Status.ACCEPTED,
        )

    except Exception as e:
        logger.error(f"Failed to queue agent task: {e}")
        return Response.error(
            message="Failed to queue agent task",
            data={"error": str(e)},
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
