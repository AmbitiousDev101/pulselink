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


async def close_redis():
    """Close the Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def get_cached(url_hash: str) -> dict | None:
    """Get a cached URL analysis result by hash."""
    client = await get_redis()
    try:
        data = await client.get(f"url:{url_hash}")
        if data:
            logger.debug(f"Cache hit for {url_hash}")
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
    return None


async def set_cached(url_hash: str, result: dict, ttl: int = 3600):
    """Cache a URL analysis result with TTL."""
    client = await get_redis()
    try:
        await client.set(
            f"url:{url_hash}",
            json.dumps(result, default=str),
            ex=ttl,
        )
        logger.debug(f"Cached result for {url_hash}, TTL={ttl}s")
    except Exception as e:
        logger.error(f"Redis set error: {e}")


async def check_rate_limit(ip: str, limit: int = 20, window: int = 60) -> bool:
    """
    Sliding window rate limiter using Redis INCR.
    Returns True if the request is allowed, False if rate limited.
    """
    client = await get_redis()
    key = f"ratelimit:{ip}"
    try:
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, window)
        if current > limit:
            logger.warning(f"Rate limit exceeded for {ip}: {current}/{limit}")
            return False
        return True
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True  # fail open


async def is_redis_healthy() -> bool:
    """Check if Redis is reachable."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False
