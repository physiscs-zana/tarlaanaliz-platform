# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# BOLUM 3: AuditLogRepository SQLAlchemy implementation — WORM (append-only).
# KR-062: Denetlenebilirlik.
"""AuditLogRepository port implementation using SQLAlchemy async."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src.core.domain.entities.audit_log_entry import AuditLogEntry
from src.core.ports.repositories.audit_log_repository import AuditLogRepository
from src.infrastructure.persistence.sqlalchemy.base import Base


class AuditLogModel(Base):
    """audit_logs tablosu ORM modeli (BOLUM 3, KR-062).

    WORM (Write Once Read Many): update ve delete YOKTUR.
    PII ICERMEZ; actor_id_hash tek-yonlu kimliktir.
    """

    __tablename__ = "audit_logs"

    audit_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_action: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    field_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    mission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    card_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    change_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(120), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class AuditLogRepositoryImpl(AuditLogRepository):
    """AuditLogRepository portunun async SQLAlchemy implementasyonu (BOLUM 3, KR-062).

    WORM garantisi: yalnizca append ve read islemleri var.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_entity(self, model: AuditLogModel) -> AuditLogEntry:
        """ORM modelini domain entity'sine donusturur."""
        return AuditLogEntry(
            audit_log_id=model.audit_log_id,
            event_type=model.event_type,
            event_action=model.event_action,
            outcome=model.outcome,
            correlation_id=model.correlation_id,
            actor_type=model.actor_type,
            actor_id_hash=model.actor_id_hash,
            created_at=model.created_at,
            field_id=model.field_id,
            mission_id=model.mission_id,
            batch_id=model.batch_id,
            card_id=model.card_id,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            change_details=model.change_details,
            error_code=model.error_code,
            error_message=model.error_message,
            http_status=model.http_status,
            latency_ms=model.latency_ms,
        )

    # ------------------------------------------------------------------
    # Yazma (append-only)
    # ------------------------------------------------------------------

    async def append(self, entry: AuditLogEntry) -> None:
        """Yeni denetim logu ekle (WORM: yalnizca yazma)."""
        model = AuditLogModel(
            audit_log_id=entry.audit_log_id,
            event_type=entry.event_type,
            event_action=entry.event_action,
            outcome=entry.outcome,
            correlation_id=entry.correlation_id,
            actor_type=entry.actor_type,
            actor_id_hash=entry.actor_id_hash,
            field_id=entry.field_id,
            mission_id=entry.mission_id,
            batch_id=entry.batch_id,
            card_id=entry.card_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            change_details=entry.change_details,
            error_code=entry.error_code,
            error_message=entry.error_message,
            http_status=entry.http_status,
            latency_ms=entry.latency_ms,
        )
        self._session.add(model)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------

    async def find_by_id(self, audit_log_id: uuid.UUID) -> Optional[AuditLogEntry]:
        """audit_log_id ile AuditLogEntry getir."""
        model = await self._session.get(AuditLogModel, audit_log_id)
        return self._to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Liste sorgulari
    # ------------------------------------------------------------------

    async def list_by_correlation_id(self, correlation_id: str) -> List[AuditLogEntry]:
        """Bir correlation_id'ye ait tum loglari getir."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.correlation_id == correlation_id)
            .order_by(AuditLogModel.created_at.asc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> List[AuditLogEntry]:
        """Belirli bir kaynaga ait tum loglari getir."""
        result = await self._session.execute(
            select(AuditLogModel)
            .where(
                AuditLogModel.resource_type == resource_type,
                AuditLogModel.resource_id == resource_id,
            )
            .order_by(AuditLogModel.created_at.asc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_actor(
        self,
        actor_id_hash: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Bir aktore ait loglari getir (zaman araligi opsiyonel)."""
        stmt = select(AuditLogModel).where(AuditLogModel.actor_id_hash == actor_id_hash)
        if since is not None:
            stmt = stmt.where(AuditLogModel.created_at >= since)
        if until is not None:
            stmt = stmt.where(AuditLogModel.created_at < until)
        stmt = stmt.order_by(AuditLogModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_event_type(
        self,
        event_type: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Belirli event_type'a gore loglari getir."""
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == event_type)
        if since is not None:
            stmt = stmt.where(AuditLogModel.created_at >= since)
        if until is not None:
            stmt = stmt.where(AuditLogModel.created_at < until)
        stmt = stmt.order_by(AuditLogModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
