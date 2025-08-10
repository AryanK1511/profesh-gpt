import json
from typing import Optional

from src.common.logger import logger
from src.database.redis.redis_client import RedisClient
from src.modules.agent.schemas.agent_schemas import AgentEvent


class AgentStatusRepository:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    def _get_channel_name(
        self, run_id: str, channel_type: str = "agent_progress"
    ) -> str:
        return f"{channel_type}:{run_id}"

    async def publish_event(
        self, run_id: str, event: AgentEvent, channel_type: str = "agent_progress"
    ) -> bool:
        try:
            channel = self._get_channel_name(run_id, channel_type)
            message = event.model_dump_json()
            await self.redis_client.publish(channel, message)
            logger.debug(f"Published event {event.event_type} to channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def subscribe_to_channel(
        self, run_id: str, channel_type: str = "agent_progress"
    ):
        try:
            channel = self._get_channel_name(run_id, channel_type)
            pubsub = await self.redis_client.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channel: {e}")
            raise

    async def unsubscribe_from_channel(
        self, run_id: str, channel_type: str = "agent_progress"
    ):
        try:
            channel = self._get_channel_name(run_id, channel_type)
            await self.redis_client.unsubscribe(channel)
            logger.info(f"Unsubscribed from channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel: {e}")

    async def get_message(self, timeout: float = 1.0) -> Optional[dict]:
        try:
            message = await self.redis_client.get_message(timeout=timeout)
            if message and message.get("type") == "message":
                return json.loads(message.get("data", "{}"))
            return None
        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            return None

    async def cleanup_channel(self, run_id: str, channel_type: str = "agent_progress"):
        try:
            await self.unsubscribe_from_channel(run_id, channel_type)
            logger.info(f"Cleaned up resources for run_id: {run_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup channel: {e}")
