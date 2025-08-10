import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.common.logger import logger
from src.database.redis.redis_client import redis_client
from src.modules.agent.respositories.agent_status_repository import (
    AgentStatusRepository,
)

router = APIRouter(prefix="/agent", tags=["agent-websocket"])

active_connections: Dict[str, WebSocket] = {}


@router.websocket("/stream/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()
    active_connections[run_id] = websocket

    repository = AgentStatusRepository(redis_client=redis_client)

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
