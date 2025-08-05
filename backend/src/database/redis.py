import redis.asyncio as redis
from src.common.config import settings
from src.common.logger import logger


class RedisManager:
    def __init__(self):
        self.redis_client: redis.Redis = None
        self.pubsub: redis.client.PubSub = None

    async def connect(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def publish(self, channel: str, message: str):
        if not self.redis_client:
            await self.connect()
        await self.redis_client.publish(channel, message)

    async def subscribe(self, channel: str):
        if not self.redis_client:
            await self.connect()
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(channel)
        return self.pubsub

    async def unsubscribe(self, channel: str):
        if self.pubsub:
            await self.pubsub.unsubscribe(channel)
            await self.pubsub.close()

    async def get_message(self, timeout: float = 1.0):
        if self.pubsub:
            return await self.pubsub.get_message(timeout=timeout)
        return None


redis_manager = RedisManager()
