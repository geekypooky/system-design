import redis.asyncio as redis
from typing import Optional

redis_client: Optional[redis.Redis] = None

async def init_redis(url: str):
    global redis_client
    redis_client = redis.from_url(url)

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()

def get_redis() -> redis.Redis:
    if not redis_client:
        raise Exception("Redis not initialized")
    return redis_client
