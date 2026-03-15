# PATH: src/infrastructure/persistence/redis/cache.py
# DESC: Redis cache adapter.
"""Async Redis client management with connection pooling.

Provides a singleton Redis client for caching, rate limiting,
brute-force tracking, and webhook replay protection.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from src.infrastructure.config.settings import Settings, get_settings

_client: aioredis.Redis | None = None


async def get_redis_client(settings: Settings | None = None) -> aioredis.Redis:
    """Return the singleton async Redis client."""
    global _client
    if _client is None:
        _settings = settings or get_settings()
        _client = aioredis.from_url(
            _settings.redis_url,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _client


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
