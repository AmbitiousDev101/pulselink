import os
import json
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def set_cached(url_hash: str, result: dict, ttl: int = 3600):
    """Cache a URL analysis result with TTL."""
    client = await get_redis()
    try:
        await client.set(
            f"url:{url_hash}",
            json.dumps(result, default=str),
            ex=ttl,
        )
        logger.info(f"Redis cache updated for {url_hash}, TTL={ttl}s")
    except Exception as e:
        logger.error(f"Redis set error: {e}")


async def close_redis():
    """Close the Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
