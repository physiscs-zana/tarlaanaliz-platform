# PATH: src/infrastructure/persistence/sqlalchemy/unit_of_work.py
# DESC: Transaction sinirari ve atomicity (Unit of Work).
"""Unit of Work pattern implementation for transactional consistency.

Ensures that all repository operations within a business transaction
are committed or rolled back atomically. Domain events are collected
and published only after successful commit.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_session_factory


class UnitOfWork:
    """Manages a single transactional boundary.

    Usage::

        async with unit_of_work() as uow:
            repo = FieldRepositoryImpl(uow.session)
            repo.add(field_entity)
            uow.collect_event(field_created_event)
            await uow.commit()
        # events are available via uow.collected_events after commit
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events: list[Any] = []
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        return self._session

    def collect_event(self, event: Any) -> None:
        """Collect a domain event to be published after commit."""
        self._events.append(event)

    async def commit(self) -> None:
        """Commit the transaction."""
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Rollback the transaction."""
        await self._session.rollback()

    @property
    def committed(self) -> bool:
        return self._committed

    @property
    def collected_events(self) -> list[Any]:
        """Return collected events (only meaningful after commit)."""
        return list(self._events)


@asynccontextmanager
async def unit_of_work() -> AsyncIterator[UnitOfWork]:
    """Create a new Unit of Work with a fresh session.

    On exception, the session is rolled back and events are discarded.
    """
    factory = await get_session_factory()
    session = factory()
    uow = UnitOfWork(session)
    try:
        yield uow
    except Exception:
        await uow.rollback()
        raise
    finally:
        await session.close()
