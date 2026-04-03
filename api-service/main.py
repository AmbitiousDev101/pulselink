import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, close_db
from services.kafka_producer import init_producer, close_producer
from services.cache import close_redis
from services.websocket_manager import ws_manager
from routes import urls, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    logger.info(f"Starting PulseLink API ({ENVIRONMENT})")

    await init_db()
    logger.info("Database initialized")

    await init_producer()
    logger.info("Kafka producer initialized")

    await ws_manager.start_kafka_consumer()
    logger.info("WebSocket Kafka consumer started")

    yield

    # Shutdown
    logger.info("Shutting down PulseLink API")
    await ws_manager.stop()
    await close_producer()
    await close_redis()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="PulseLink API",
    description="Real-time URL analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(urls.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "service": "PulseLink API",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """WebSocket endpoint for live feed of analysis results."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client messages (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
