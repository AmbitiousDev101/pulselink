import os
import json
import asyncio
import logging
from fastapi import WebSocket
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._consumer_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self._connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients."""
        if not self._connections:
            return

        disconnected = []
        data = json.dumps(message, default=str)

        for ws in self._connections:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)

    async def start_kafka_consumer(self):
        """Start a background Kafka consumer on 'url.analyzed' topic."""
        self._consumer_task = asyncio.create_task(self._consume_loop())
        logger.info("WebSocket Kafka consumer task started")

    async def _consume_loop(self):
        """Consume messages from 'url.analyzed' and broadcast to clients."""
        consumer = None
        while True:
            try:
                consumer = AIOKafkaConsumer(
                    "url.analyzed",
                    bootstrap_servers=KAFKA_BROKERS,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    group_id="websocket-feed",
                    auto_offset_reset="latest",
                )
                await consumer.start()
                logger.info("WebSocket Kafka consumer connected")

                async for msg in consumer:
                    try:
                        from services.cache import set_cached
                        data = msg.value
                        url_hash = data.get("url_hash")
                        if not url_hash and "url" in data:
                            import hashlib
                            url_hash = hashlib.sha256(data["url"].strip().lower().rstrip("/").encode()).hexdigest()
                        if url_hash:
                            await set_cached(url_hash, data, ttl=3600)
                            
                        await self.broadcast(data)
                    except Exception as e:
                        logger.error(f"Broadcast error: {e}")

            except asyncio.CancelledError:
                logger.info("WebSocket Kafka consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Kafka consumer error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)
            finally:
                if consumer:
                    try:
                        await consumer.stop()
                    except Exception:
                        pass

    async def stop(self):
        """Stop the consumer task and close all connections."""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        for ws in self._connections[:]:
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()
        logger.info("WebSocket manager stopped")


# Global instance
ws_manager = WebSocketManager()
