# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Async database engine with connection pooling.
# PATH: src/infrastructure/persistence/database.py
# DESC: Async database engine factory with connection pooling.
"""Database engine management for async SQLAlchemy (asyncpg).

Production-grade connection pool with statement timeouts,
SSL support, and health check integration.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config.settings import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine with production-safe defaults."""
    connect_args: dict[str, Any] = {
        "statement_cache_size": 0,
        "command_timeout": 30,
    }
    if settings.environment == "production":
        connect_args["ssl"] = "prefer"

    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=settings.db_echo,
        connect_args=connect_args,
    )


async def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the singleton async engine, creating it on first call."""
    global _engine
    if _engine is None:
        _settings = settings or get_settings()
        _engine = _build_engine(_settings)
    return _engine


async def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the singleton session factory."""
    global _session_factory
    if _session_factory is None:
        engine = await get_engine(settings)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def dispose_engine() -> None:
    """Dispose engine on shutdown (close all pooled connections)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
