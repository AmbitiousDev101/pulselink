import hashlib
import json
import logging
import random
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, Response

from models import (
    URLSubmit,
    URLSubmitResponse,
    URLResponse,
    URLResult,
    PaginatedURLResponse,
)
from database import get_pool
from services.cache import get_cached, set_cached, check_rate_limit
from services.kafka_producer import publish_url_submitted, publish_result_ready
from services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["urls"])


def _hash_url(url: str) -> str:
    """Create a SHA-256 hash of the normalized URL."""
    normalized = url.strip().lower().rstrip("/")
    return hashlib.sha256(normalized.encode()).hexdigest()


@router.post("/urls")
async def submit_url(body: URLSubmit, request: Request, response: Response):
    """
    Submit a URL for analysis.
    - Check rate limit
    - Check Redis cache
    - If cached, return result immediately (200)
    - If not cached, publish to Kafka and return 202 with job_id
    """
    if not (body.url.startswith("http://") or body.url.startswith("https://")):
        raise HTTPException(status_code=422, detail="Invalid URL format. Must start with http:// or https://")

    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting
    allowed = await check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    url_hash = _hash_url(body.url)

    # Check cache
    cached = await get_cached(url_hash)
    if cached:
        response.status_code = 200
        # Return full URLResponse
        return cached

    # Check if already in DB
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, status FROM urls WHERE url_hash = $1", url_hash
        )

        if existing:
            return URLSubmitResponse(
                job_id=existing["id"],
                status=existing["status"],
                message="Analysis already submitted",
            )

        # Insert new URL job
        row = await conn.fetchrow(
            """
            INSERT INTO urls (url, url_hash, status)
            VALUES ($1, $2, 'processing')
            RETURNING id
            """,
            body.url,
            url_hash,
        )
        job_id = row["id"]

    # Publish to Kafka
    await publish_url_submitted(str(job_id), body.url)

    response.status_code = 202
    return URLSubmitResponse(
        job_id=job_id,
        status="processing",
        message="URL submitted for analysis",
    )


@router.get("/urls/{url_id}", response_model=URLResponse)
async def get_url_result(url_id: UUID):
    """Fetch a specific URL analysis result by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, url, url_hash, status, created_at, result FROM urls WHERE id = $1",
            url_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="URL analysis not found")

    result_data = None
    if row["result"]:
        result_dict = json.loads(row["result"]) if isinstance(row["result"], str) else row["result"]
        result_data = URLResult(**result_dict)

    return URLResponse(
        id=row["id"],
        url=row["url"],
        url_hash=row["url_hash"],
        status=row["status"],
        created_at=row["created_at"],
        result=result_data,
    )


@router.get("/urls", response_model=PaginatedURLResponse)
async def list_urls(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Paginated list of all completed URL analyses."""
    pool = await get_pool()
    offset = (page - 1) * limit

    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM urls WHERE status = 'completed'"
        )
        rows = await conn.fetch(
            """
            SELECT id, url, url_hash, status, created_at, result
            FROM urls
            WHERE status = 'completed'
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

    items = []
    for row in rows:
        result_data = None
        if row["result"]:
            result_dict = json.loads(row["result"]) if isinstance(row["result"], str) else row["result"]
            result_data = URLResult(**result_dict)
        items.append(
            URLResponse(
                id=row["id"],
                url=row["url"],
                url_hash=row["url_hash"],
                status=row["status"],
                created_at=row["created_at"],
                result=result_data,
            )
        )

    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedURLResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post("/simulate", response_model=dict)
async def simulate_traffic():
    """Generate 5 fake URL analyses for demo purposes."""
    pool = await get_pool()
    
    fake_data = [
        {
            "url": "https://github.com",
            "title": "GitHub: Let's build from here",
            "safety_score": "safe",
            "status_code": 200,
            "response_time_ms": 42.5,
            "redirect_chain": [],
            "ssl_valid": True,
            "tech_stack": ["Ruby on Rails", "React", "NGINX"],
        },
        {
            "url": "http://suspicious-login.example.com",
            "title": "Account Login",
            "safety_score": "suspicious",
            "status_code": 200,
            "response_time_ms": 312.0,
            "redirect_chain": ["http://redirect1.com"],
            "ssl_valid": False,
            "tech_stack": ["PHP", "Apache"],
        },
        {
            "url": "https://stripe.com",
            "title": "Stripe | Financial Infrastructure for the Internet",
            "safety_score": "safe",
            "status_code": 200,
            "response_time_ms": 85.2,
            "redirect_chain": [],
            "ssl_valid": True,
            "tech_stack": ["React", "Next.js", "Express"],
        },
        {
            "url": "https://malicious-crypto-giveaway.tv",
            "title": "FREE BITCOIN GIVEAWAY",
            "safety_score": "dangerous",
            "status_code": 200,
            "response_time_ms": 1150.0,
            "redirect_chain": [],
            "ssl_valid": True,
            "tech_stack": ["WordPress", "MySQL"],
        },
        {
            "url": "https://ycombinator.com",
            "title": "Y Combinator",
            "safety_score": "safe",
            "status_code": 200,
            "response_time_ms": 65.0,
            "redirect_chain": ["https://www.ycombinator.com"],
            "ssl_valid": True,
            "tech_stack": ["Ruby", "Puma", "Cloudflare"],
        }
    ]

    import asyncio
    
    async with pool.acquire() as conn:
        for idx, item in enumerate(fake_data):
            # random id and hash
            job_id = uuid4()
            url_hash = _hash_url(item["url"] + str(random.random()))
            
            result_payload = {
                "id": str(job_id),
                "url": item["url"],
                "title": item["title"],
                "safety_score": item["safety_score"],
                "status_code": item["status_code"],
                "response_time_ms": item["response_time_ms"],
                "redirect_chain": item["redirect_chain"],
                "ssl_valid": item["ssl_valid"],
                "ssl_expires_at": None,
                "tech_stack": item["tech_stack"],
                "screenshot_url": None,
                "analyzed_at": datetime.now().isoformat(),
                "description": None,
            }
            
            # Insert into database
            await conn.execute(
                """
                INSERT INTO urls (id, url, url_hash, status, result)
                VALUES ($1, $2, $3, 'completed', $4)
                """,
                job_id,
                item["url"],
                url_hash,
                json.dumps(result_payload)
            )
            
            # Format payload for the frontend live feed (which expects the same format as DB row)
            feed_payload = {
                "id": str(job_id),
                "url": item["url"],
                "url_hash": url_hash,
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "result": result_payload
            }
            
            await publish_result_ready(feed_payload)
            await asyncio.sleep(0.3)  # slight delay to look natural on the live feed
            
    return {"status": "simulated", "count": 5}

# Websocket endpoint moved to main.py
