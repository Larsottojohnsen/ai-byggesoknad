import json
from typing import Any, Optional
import redis.asyncio as aioredis
from core.config import settings
import structlog

logger = structlog.get_logger()

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        val = await r.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning("cache_get_error", key=key, error=str(e))
    return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("cache_set_error", key=key, error=str(e))


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning("cache_delete_error", key=key, error=str(e))
