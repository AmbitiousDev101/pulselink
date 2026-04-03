import os
import json
import logging
import asyncpg
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from analyzer import analyze_url

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pulselink:pulselink123@localhost:5432/pulselink"
)


def _parse_dsn(url: str) -> dict:
    """Parse DATABASE_URL into asyncpg connect kwargs."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
        "host": parsed.hostname,
        "port": parsed.port or 5432,
    }


async def run_consumer():
    """
    Main consumer loop:
    1. Consume from 'url.submitted'
    2. Analyze the URL
    3. Write result to PostgreSQL
    4. Publish result to 'url.analyzed'
    """
    # Connect to PostgreSQL
    db_params = _parse_dsn(DATABASE_URL)
    pool = await asyncpg.create_pool(**db_params, min_size=1, max_size=5)
    logger.info("Database pool created")

    # Create Kafka consumer
    consumer = AIOKafkaConsumer(
        "url.submitted",
        bootstrap_servers=KAFKA_BROKERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="worker-group",
        auto_offset_reset="earliest",
    )

    # Create Kafka producer (for publishing results)
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )

    import asyncio
    while True:
        try:
            await consumer.start()
            await producer.start()
            logger.info(f"Worker consumer started on {KAFKA_BROKERS}")
            break
        except Exception as e:
            logger.error(f"Failed to connect to Kafka, retrying in 5s: {e}")
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            job_id = msg.value.get("job_id")
            url = msg.value.get("url")

            if not job_id or not url:
                logger.warning(f"Invalid message: {msg.value}")
                continue

            logger.info(f"Processing job {job_id}: {url}")

            try:
                # Analyze the URL
                result = await analyze_url(url)

                # Write result to PostgreSQL
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE urls
                        SET status = 'completed', result = $1::jsonb
                        WHERE id = $2
                        """,
                        json.dumps(result, default=str),
                        __import__("uuid").UUID(job_id),
                    )
                logger.info(f"Job {job_id} completed and saved to DB")

                # Publish to url.analyzed for WebSocket broadcast
                from datetime import datetime, timezone
                import hashlib
                broadcast_msg = {
                    "id": str(job_id),
                    "url": url,
                    "url_hash": hashlib.sha256(url.strip().lower().rstrip("/").encode()).hexdigest(),
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "result": result,
                }
                await producer.send_and_wait(
                    topic="url.analyzed",
                    key=job_id,
                    value=broadcast_msg,
                )
                logger.info(f"Job {job_id} result published to url.analyzed")

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)

                # Mark as failed in DB
                try:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            """
                            UPDATE urls
                            SET status = 'failed', result = $1::jsonb
                            WHERE id = $2
                            """,
                            json.dumps({"error": str(e)}),
                            __import__("uuid").UUID(job_id),
                        )
                except Exception:
                    logger.error(f"Failed to mark job {job_id} as failed")

    except Exception as e:
        logger.error(f"Consumer loop error: {e}", exc_info=True)
    finally:
        await consumer.stop()
        await producer.stop()
        await pool.close()
        logger.info("Worker consumer stopped")
