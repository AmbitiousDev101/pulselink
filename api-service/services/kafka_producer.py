import os
import json
import logging
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

_producer: AIOKafkaProducer | None = None


import asyncio
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

async def init_producer():
    """Initialize the Kafka producer and create topics."""
    global _producer

    # Create topics if they don't exist, retry if connection fails
    while True:
        try:
            admin = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BROKERS)
            await admin.start()
            try:
                topics = await admin.list_topics()
                new_topics = []
                if "url.submitted" not in topics:
                    new_topics.append(NewTopic(name="url.submitted", num_partitions=1, replication_factor=1))
                if "url.analyzed" not in topics:
                    new_topics.append(NewTopic(name="url.analyzed", num_partitions=1, replication_factor=1))
                if new_topics:
                    await admin.create_topics(new_topics)
                    logger.info(f"Created topics: {[t.name for t in new_topics]}")
            finally:
                await admin.close()
            break
        except Exception as e:
            logger.warning(f"Failed to create topics, retrying in 5s: {e}")
            await asyncio.sleep(5)

    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    
    while True:
        try:
            await _producer.start()
            logger.info(f"Kafka producer connected to {KAFKA_BROKERS}")
            break
        except Exception as e:
            logger.error(f"Kafka producer connection failed, retrying in 5s: {e}")
            await asyncio.sleep(5)


async def close_producer():
    """Stop and close the Kafka producer."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer closed")


async def publish_url_submitted(job_id: str, url: str):
    """Publish a URL submission event to the 'url.submitted' topic."""
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized")
    message = {
        "job_id": job_id,
        "url": url,
    }
    await _producer.send_and_wait(
        topic="url.submitted",
        key=job_id,
        value=message,
    )
    logger.info(f"Published url.submitted: job_id={job_id}")


async def publish_result_ready(result: dict):
    """Publish a completed analysis result to the 'url.analyzed' topic."""
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized")
    await _producer.send_and_wait(
        topic="url.analyzed",
        key=str(result.get("id", "")),
        value=result,
    )
    logger.info(f"Published url.analyzed: id={result.get('id')}")


async def is_kafka_healthy() -> bool:
    """Check if Kafka producer is connected."""
    return _producer is not None and _producer._sender is not None
