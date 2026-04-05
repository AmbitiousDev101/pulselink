"""Tests for PulseLink API service URL endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
import uuid
import json
from datetime import datetime


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
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_db_mock(fetchrow_result=None, fetchrow_side_effect=None):
    conn = AsyncMock()
    if fetchrow_side_effect:
        conn.fetchrow = AsyncMock(side_effect=fetchrow_side_effect)
    else:
        conn.fetchrow = AsyncMock(return_value=fetchrow_result)
    conn.fetchval = AsyncMock(return_value=1)
    conn.execute = AsyncMock(return_value=None)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=conn)
    ctx.__aexit__ = AsyncMock(return_value=False)

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=ctx)

    async def get_pool_func():
        return pool

    return get_pool_func


@pytest.mark.anyio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "PulseLink API"


@pytest.mark.anyio
async def test_health_endpoint(client):
    with patch("routes.health.get_pool", new=make_db_mock()), \
         patch("routes.health.is_kafka_healthy", return_value=True), \
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
    mock_id = uuid.uuid4()
    get_pool = make_db_mock(fetchrow_side_effect=[
        None,
        {"id": mock_id, "status": "processing"}
    ])
    with patch("routes.urls.get_pool", new=get_pool), \
         patch("routes.urls.check_rate_limit", new_callable=AsyncMock, return_value=True), \
         patch("routes.urls.get_cached", new_callable=AsyncMock, return_value=None), \
         patch("routes.urls.publish_url_submitted", new_callable=AsyncMock):
        response = await client.post("/api/v1/urls", json={"url": "https://example.com"})
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"


@pytest.mark.anyio
async def test_get_url_not_found(client):
    get_pool = make_db_mock(fetchrow_result=None)
    with patch("routes.urls.get_pool", new=get_pool):
        response = await client.get(f"/api/v1/urls/{uuid.uuid4()}")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_get_url_result(client):
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
    get_pool = make_db_mock(fetchrow_result=mock_row)
    with patch("routes.urls.get_pool", new=get_pool):
        response = await client.get(f"/api/v1/urls/{test_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_id)
        assert data["status"] == "completed"
        assert data["result"]["title"] == "Example Domain"
