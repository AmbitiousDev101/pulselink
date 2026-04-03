import logging
from fastapi import APIRouter
from models import HealthResponse
from services.cache import is_redis_healthy
from services.kafka_producer import is_kafka_healthy
from database import get_pool

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — reports status of all dependencies."""
    redis_ok = False
    try:
        redis_ok = bool(await is_redis_healthy())
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")

    kafka_ok = False
    try:
        kafka_ok = bool(is_kafka_healthy())
    except Exception as e:
        logger.warning(f"Kafka health check failed: {e}")

    db_ok = False
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.warning(f"DB health check failed: {e}")

    overall = "ok" if (redis_ok and kafka_ok and db_ok) else "degraded"

    return HealthResponse(
        status=overall,
        kafka=kafka_ok,
        redis=redis_ok,
        db=db_ok,
    )
