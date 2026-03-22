# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050 / SC-SEC-02: Distributed brute-force protection via Redis.
"""Redis-backed brute force tracker that works across multiple workers/pods."""

from __future__ import annotations

import logging
import time

LOGGER = logging.getLogger("security.brute_force")

_BF_PREFIX = "bf:"
_BF_LOCK_PREFIX = "bf_lock:"
_MAX_ATTEMPTS = 16
_LOCKOUT_SECONDS = 30 * 60  # 30 minutes
_WINDOW_SECONDS = 30 * 60  # 30 minutes


async def check_lockout(phone: str) -> tuple[bool, int]:
    """Check if phone is locked out. Returns (is_locked, retry_after_seconds)."""
    try:
        from src.infrastructure.persistence.redis.cache import get_redis_client

        client = await get_redis_client()
        lock_key = f"{_BF_LOCK_PREFIX}{phone}"
        ttl = await client.ttl(lock_key)
        if ttl > 0:
            return True, ttl
        return False, 0
    except Exception:
        LOGGER.warning("brute_force_check_failed")
        return False, 0  # Fail-open


async def record_failure(phone: str) -> tuple[bool, int]:
    """Record a failed login attempt. Returns (is_now_locked, retry_after_seconds)."""
    try:
        from src.infrastructure.persistence.redis.cache import get_redis_client

        client = await get_redis_client()

        attempts_key = f"{_BF_PREFIX}{phone}"
        now = time.time()

        pipe = client.pipeline(transaction=True)
        pipe.zremrangebyscore(attempts_key, "-inf", now - _WINDOW_SECONDS)
        pipe.zadd(attempts_key, {f"{now}": now})
        pipe.zcard(attempts_key)
        pipe.expire(attempts_key, _WINDOW_SECONDS + 60)
        results = await pipe.execute()

        count = results[2]

        if count >= _MAX_ATTEMPTS:
            lock_key = f"{_BF_LOCK_PREFIX}{phone}"
            await client.setex(lock_key, _LOCKOUT_SECONDS, "1")
            LOGGER.warning(
                "AUTH.LOCKOUT",
                extra={"event": "AUTH.LOCKOUT", "attempts": count},
            )
            return True, _LOCKOUT_SECONDS

        return False, 0
    except Exception:
        LOGGER.warning("brute_force_record_failed")
        return False, 0


async def record_success(phone: str) -> None:
    """Clear attempt tracking on successful login."""
    try:
        from src.infrastructure.persistence.redis.cache import get_redis_client

        client = await get_redis_client()
        await client.delete(f"{_BF_PREFIX}{phone}", f"{_BF_LOCK_PREFIX}{phone}")
    except Exception:
        LOGGER.warning("brute_force_clear_failed")
