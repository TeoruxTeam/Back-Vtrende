from contextlib import asynccontextmanager
from typing import AsyncGenerator
from redis.asyncio import Redis


class RedisPool:
    def __init__(self, redis_url: str) -> None:
        self._redis: Redis = Redis.from_url(redis_url)

    @asynccontextmanager
    async def get_redis(self) -> AsyncGenerator[Redis, None]:
        try:
            yield self._redis
        except Exception as e:
            raise e

    async def close(self):
        await self._redis.close()
