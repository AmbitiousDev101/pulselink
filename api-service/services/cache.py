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
    Sliding window rate limiter using Redis Sorted Sets (ZSET).
    Returns True if the request is allowed, False if rate limited.
    """
    import time
    client = await get_redis()
    key = f"ratelimit:{ip}"
    now = time.time()
    
    try:
        pipe = client.pipeline()
        # Remove timestamps older than the window
        pipe.zremrangebyscore(key, 0, now - window)
        # Add current timestamp (random suffix to avoid collisions if multiple requests at same exact float time)
        import random
        timestamp_key = f"{now}:{random.random()}"
        pipe.zadd(key, {timestamp_key: now})
        # Count remaining timestamps
        pipe.zcard(key)
        # Set expiry for cleanup
        pipe.expire(key, window)
        
        results = await pipe.execute()
        count = results[2] # result of zcard
        
        if count > limit:
            logger.warning(f"Sliding window rate limit exceeded for {ip}: {count}/{limit}")
            return False
        return True
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        # Log stack trace if needed
        import traceback
        logger.error(traceback.format_exc())
        return True  # fail open



async def is_redis_healthy() -> bool:
    """Check if Redis is reachable."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False
