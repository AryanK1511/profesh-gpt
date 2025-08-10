import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.common.logger import logger
from src.modules.agent.dependencies.agent_dependencies import AgentStatusRepo

router = APIRouter(prefix="/agent", tags=["agent-websocket"])

active_connections: Dict[str, WebSocket] = {}


@router.websocket("/stream/{run_id}")
async def websocket_endpoint(
    websocket: WebSocket, run_id: str, repository: AgentStatusRepo
):
    await websocket.accept()
    active_connections[run_id] = websocket

    try:
        logger.info(f"WebSocket connected for run_id: {run_id}")
        await repository.subscribe_to_channel(run_id)

        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "run_id": run_id,
                    "message": "Connected to agent stream",
                }
            )
        )

        while True:
            try:
                message = await repository.get_message(timeout=1.0)

                if message:
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"Forwarded event to WebSocket for run_id: {run_id}")

                if websocket.client_state.value == 3:
                    break

            except Exception as e:
                logger.error(f"Error processing message for run_id {run_id}: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run_id: {run_id}")
    except Exception as e:
        logger.error(f"WebSocket error for run_id {run_id}: {e}")
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "run_id": run_id,
                        "message": f"WebSocket error: {str(e)}",
                    }
                )
            )
        except Exception:
            pass
    finally:
        if run_id in active_connections:
            del active_connections[run_id]
        await repository.unsubscribe_from_channel(run_id)
        logger.info(f"Cleaned up WebSocket connection for run_id: {run_id}")


@router.websocket("/processing/{task_id}")
async def agent_processing_websocket(
    websocket: WebSocket, task_id: str, repository: AgentStatusRepo
):
    await websocket.accept()
    active_connections[task_id] = websocket

    try:
        logger.info(f"Agent processing WebSocket connected for task_id: {task_id}")
        await repository.subscribe_to_channel(task_id, "agent_processing")

        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "task_id": task_id,
                    "message": "Connected to agent processing stream",
                }
            )
        )

        while True:
            try:
                message = await repository.get_message(timeout=1.0)

                if message:
                    await websocket.send_text(json.dumps(message))
                    logger.debug(
                        f"Forwarded processing event to WebSocket for task_id: {task_id}"
                    )

                if websocket.client_state.value == 3:
                    break

            except Exception as e:
                logger.error(f"Error processing message for task_id {task_id}: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Agent processing WebSocket disconnected for task_id: {task_id}")
    except Exception as e:
        logger.error(f"Agent processing WebSocket error for task_id {task_id}: {e}")
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "task_id": task_id,
                        "message": f"WebSocket error: {str(e)}",
                    }
                )
            )
        except Exception:
            pass
    finally:
        if task_id in active_connections:
            del active_connections[task_id]
        await repository.unsubscribe_from_channel(task_id, "agent_processing")
        logger.info(
            f"Cleaned up agent processing WebSocket connection for task_id: {task_id}"
        )
