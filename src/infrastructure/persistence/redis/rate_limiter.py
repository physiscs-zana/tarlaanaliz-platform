# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: Distributed rate limiter for brute-force protection.
# PATH: src/infrastructure/persistence/redis/rate_limiter.py
# DESC: Redis-backed distributed rate limiter.
"""Distributed sliding-window rate limiter using Redis sorted sets.

Works correctly across multiple Uvicorn workers and pods.
Implements the RateLimitStore protocol from rate_limit_middleware.
"""

from __future__ import annotations

import time

import redis.asyncio as aioredis


class RedisRateLimitStore:
    """Redis-backed sliding window rate limiter using sorted sets."""

    def __init__(self, client: aioredis.Redis, key_prefix: str = "rl:") -> None:
        self._client = client
        self._prefix = key_prefix

    async def allow_async(self, key: str, now: float, per_minute: int, burst: int) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, retry_after_seconds)."""
        limit = max(1, per_minute + burst)
        redis_key = f"{self._prefix}{key}"
        window_start = now - 60.0
        member = f"{now}:{time.monotonic_ns()}"

        pipe = self._client.pipeline(transaction=True)
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, 120)
        results = await pipe.execute()

        current_count = results[1]

        if current_count >= limit:
            await self._client.zrem(redis_key, member)
            oldest = await self._client.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = max(1, int(60 - (now - oldest[0][1])) + 1)
            else:
                retry_after = 1
            return False, retry_after

        return True, 0

    def allow(self, key: str, now: float, per_minute: int, burst: int) -> tuple[bool, int]:
        """Sync compatibility stub. Use allow_async in production."""
        return True, 0
