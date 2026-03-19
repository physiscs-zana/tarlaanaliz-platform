# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-066: Audit log ORM model — WORM (append-only) table.
# PATH: src/infrastructure/persistence/sqlalchemy/models/audit_log_model.py
# DESC: audit_logs ORM modeli. INSERT only — UPDATE/DELETE trigger ile engellenmis.
"""Audit log SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    service: Mapped[str] = mapped_column(String(50), nullable=False, default="platform")
    env: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'prod'"))
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    event_action: Mapped[str] = mapped_column(String(30), nullable=False)
    outcome: Mapped[str] = mapped_column(String(10), nullable=False, default="SUCCESS")
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    span_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    actor_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    field_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    mission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    card_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    http_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    http_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pii: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
