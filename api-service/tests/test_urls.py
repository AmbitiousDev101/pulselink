"""Tests for PulseLink API service URL endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

# Patch dependencies before importing the app
mock_pool = AsyncMock()
mock_conn = AsyncMock()


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock all external dependencies for isolated testing."""
    with patch("database.init_db", new_callable=AsyncMock) as mock_init_db, \
         patch("database.close_db", new_callable=AsyncMock), \
         patch("database.get_pool", new_callable=AsyncMock) as mock_get_pool, \
         patch("services.kafka_producer.init_producer", new_callable=AsyncMock), \
         patch("services.kafka_producer.close_producer", new_callable=AsyncMock), \
         patch("services.kafka_producer.publish_url_submitted", new_callable=AsyncMock), \
         patch("services.kafka_producer.is_kafka_healthy", return_value=True), \
         patch("services.websocket_manager.ws_manager") as mock_ws, \
         patch("services.cache.get_cached", new_callable=AsyncMock, return_value=None), \
         patch("services.cache.set_cached", new_callable=AsyncMock), \
         patch("services.cache.check_rate_limit", new_callable=AsyncMock, return_value=True), \
         patch("services.cache.is_redis_healthy", new_callable=AsyncMock, return_value=True), \
         patch("services.cache.close_redis", new_callable=AsyncMock):

        # Prepare the connection object
        mock_conn_obj = AsyncMock()

        # Prepare the context manager that yields the connection
        mock_conn_ctx = MagicMock()
        mock_conn_ctx.__aenter__ = AsyncMock(return_value=mock_conn_obj)
        mock_conn_ctx.__aexit__ = AsyncMock(return_value=False)

        # Prepare the pool which has .acquire()
        mock_pool_obj = AsyncMock()
        mock_pool_obj.acquire = MagicMock(return_value=mock_conn_ctx)
        
        mock_get_pool.return_value = mock_pool_obj

        # Mock WebSocket manager
        mock_ws.start_kafka_consumer = AsyncMock()
        mock_ws.stop = AsyncMock()

        yield {
            "pool": mock_pool_obj,
            "conn": mock_conn_obj,
            "get_pool": mock_get_pool,
        }


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client(mock_dependencies):
    """Create a test client for the FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_endpoint(client, mock_dependencies):
    """GET /health should return status info."""
    mock_dependencies["conn"].fetchval = AsyncMock(return_value=1)

    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "kafka" in data
    assert "redis" in data
    assert "db" in data


@pytest.mark.anyio
async def test_submit_url(client, mock_dependencies):
    """POST /api/v1/urls should accept a URL and return 202."""
    import uuid
    mock_row = {"id": uuid.uuid4(), "status": "processing"}

    mock_dependencies["conn"].fetchrow = AsyncMock(
        side_effect=[None, mock_row]  # First call: no existing, Second: insert returns id
    )

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
async def test_get_url_not_found(client, mock_dependencies):
    """GET /api/v1/urls/{id} should return 404 for missing IDs."""
    import uuid
    mock_dependencies["conn"].fetchrow = AsyncMock(return_value=None)

    response = await client.get(f"/api/v1/urls/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_url_result(client, mock_dependencies):
    """GET /api/v1/urls/{id} should return the analysis result."""
    import uuid
    import json
    from datetime import datetime

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
    mock_dependencies["conn"].fetchrow = AsyncMock(return_value=mock_row)

    response = await client.get(f"/api/v1/urls/{test_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_id)
    assert data["status"] == "completed"
    assert data["result"]["title"] == "Example Domain"


@pytest.mark.anyio
async def test_root_endpoint(client):
    """GET / should return service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PulseLink API"
