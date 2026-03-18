# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# SEC: Redis-backed JWT token blacklist for immediate revocation on logout.
"""Token blacklist service using Redis for distributed JWT revocation."""

from __future__ import annotations

import logging

LOGGER = logging.getLogger("security.token_blacklist")

_BLACKLIST_PREFIX = "token_blacklist:"


async def blacklist_token(token_uid: str, ttl_seconds: int) -> None:
    """Add a token to the blacklist with TTL matching remaining token lifetime."""
    try:
        from src.infrastructure.persistence.redis.cache import get_redis_client
        client = await get_redis_client()
        key = f"{_BLACKLIST_PREFIX}{token_uid}"
        await client.setex(key, ttl_seconds, "1")
        LOGGER.info("token_blacklisted", extra={"uid": token_uid[:16]})
    except Exception:
        LOGGER.warning("token_blacklist_failed", extra={"uid": token_uid[:16]})


async def is_token_blacklisted(token_uid: str) -> bool:
    """Check if a token has been revoked."""
    try:
        from src.infrastructure.persistence.redis.cache import get_redis_client
        client = await get_redis_client()
        key = f"{_BLACKLIST_PREFIX}{token_uid}"
        result = await client.exists(key)
        return bool(result)
    except Exception:
        # Fail-open: if Redis is down, allow the request (token will expire naturally)
        LOGGER.warning("token_blacklist_check_failed", extra={"uid": token_uid[:16]})
        return False
