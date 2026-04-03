import os
import asyncpg
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pulselink:pulselink123@localhost:5432/pulselink"
)

pool: asyncpg.Pool | None = None


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


async def init_db():
    """Create asyncpg connection pool and initialize tables."""
    global pool
    params = _parse_dsn(DATABASE_URL)
    pool = await asyncpg.create_pool(**params, min_size=2, max_size=10)
    logger.info("Database pool created")

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";

            CREATE TABLE IF NOT EXISTS urls (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT NOT NULL,
                url_hash TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'processing',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                result JSONB
            );

            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_urls_url_hash ON urls (url_hash);
            CREATE INDEX IF NOT EXISTS idx_urls_status ON urls (status);
            CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls (created_at DESC);
        """)
    logger.info("Database tables initialized")


async def close_db():
    """Close the database pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database pool closed")


async def get_pool() -> asyncpg.Pool:
    """Return the active connection pool."""
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool
