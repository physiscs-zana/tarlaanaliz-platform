# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Request-scoped database session management.
# PATH: src/infrastructure/persistence/sqlalchemy/session.py
# DESC: DB engine ve request-scope Session uretimi.
"""Request-scoped async session management.

Provides an async context manager for obtaining sessions from the pool.
Used by repository implementations and the Unit of Work.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session with automatic rollback on error.

    Usage::

        async with get_async_session() as session:
            result = await session.execute(...)
            await session.commit()
    """
    factory = await get_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
