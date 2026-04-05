"""Tests for PulseLink API service URL endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
import uuid
import json
from datetime import datetime

# Patch background lifecycle routines implicitly so app boots quickly
@pytest.fixture(autouse=True)
def mock_background_tasks():
    with patch("database.init_db", new_callable=AsyncMock), \
         patch("database.close_db", new_callable=AsyncMock), \
         patch("services.kafka_producer.init_producer", new_callable=AsyncMock), \
         patch("services.kafka_producer.close_producer", new_callable=AsyncMock), \
         patch("services.websocket_manager.ws_manager.start_kafka_consumer", new_callable=AsyncMock), \
         patch("services.websocket_manager.ws_manager.stop", new_callable=AsyncMock), \
         patch("services.cache.close_redis", new_callable=AsyncMock):
        yield

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create a test client for the FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class DatabaseMock:
    """Helper class to cleanly assemble an asyncpg connection payload stringently."""
    def __init__(self):
        self.conn = AsyncMock()
        
        self.ctx = MagicMock()
        self.ctx.__aenter__ = AsyncMock(return_value=self.conn)
        self.ctx.__aexit__ = AsyncMock(return_value=False)
        
        self.pool = AsyncMock()
        self.pool.acquire = MagicMock(return_value=self.ctx)


@pytest.mark.anyio
async def test_root_endpoint(client):
    """GET / should return service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PulseLink API"


@pytest.mark.anyio
async def test_health_endpoint(client):
    """GET /health should return status info."""
    db_mock = DatabaseMock()
    db_mock.conn.fetchval = AsyncMock(return_value=1)
    
    with patch("routes.health.get_pool", new_callable=AsyncMock, return_value=db_mock.pool), \
         patch("routes.health.is_kafka_healthy", new_callable=AsyncMock, return_value=True), \
         patch("routes.health.is_redis_healthy", new_callable=AsyncMock, return_value=True):
        
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "kafka" in data
        assert "redis" in data
        assert "db" in data


@pytest.mark.anyio
async def test_submit_url(client):
    """POST /api/v1/urls should accept a URL and return 202."""
    db_mock = DatabaseMock()
    mock_row = {"id": uuid.uuid4(), "status": "processing"}
    db_mock.conn.fetchrow = AsyncMock(side_effect=[None, mock_row])
    
    with patch("routes.urls.get_pool", new_callable=AsyncMock, return_value=db_mock.pool), \
         patch("routes.urls.check_rate_limit", new_callable=AsyncMock, return_value=True), \
         patch("routes.urls.get_cached", new_callable=AsyncMock, return_value=None), \
         patch("routes.urls.publish_url_submitted", new_callable=AsyncMock):
         
        response = await client.post(
            "/api/v1/urls",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        assert "message" in data


@pytest.mark.anyio
async def test_get_url_not_found(client):
    """GET /api/v1/urls/{id} should return 404 for missing IDs."""
    db_mock = DatabaseMock()
    db_mock.conn.fetchrow = AsyncMock(return_value=None)
    
    with patch("routes.urls.get_pool", new_callable=AsyncMock, return_value=db_mock.pool):
        response = await client.get(f"/api/v1/urls/{uuid.uuid4()}")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_get_url_result(client):
    """GET /api/v1/urls/{id} should return the analysis result."""
    db_mock = DatabaseMock()
    test_id = uuid.uuid4()
    mock_result = {
        "url": "https://example.com",
        "title": "Example Domain",
        "safety_score": "safe",
        "status_code": 200,
        "response_time_ms": 150.5,
        "redirect_chain": [],
        "ssl_valid": True,
        "ssl_expires_at": None,
        "tech_stack": [],
        "screenshot_url": None,
        "analyzed_at": "2026-01-01T00:00:00",
        "description": None,
    }

    mock_row = {
        "id": test_id,
        "url": "https://example.com",
        "url_hash": "abc123",
        "status": "completed",
        "created_at": datetime.now(),
        "result": json.dumps(mock_result),
    }
    db_mock.conn.fetchrow = AsyncMock(return_value=mock_row)

    with patch("routes.urls.get_pool", new_callable=AsyncMock, return_value=db_mock.pool):
        response = await client.get(f"/api/v1/urls/{test_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_id)
        assert data["status"] == "completed"
        assert data["result"]["title"] == "Example Domain"
