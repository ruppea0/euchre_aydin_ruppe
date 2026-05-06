from typing import Optional
import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class RedisClient:
    def __init__(self) -> None:
        self.client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        self.client = redis.from_url(REDIS_URL, decode_responses=True)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()

    @property
    def redis(self) -> redis.Redis:
        if self.client is None:
            raise RuntimeError("RedisClient is not connected")
        return self.client


redis_client = RedisClient()
