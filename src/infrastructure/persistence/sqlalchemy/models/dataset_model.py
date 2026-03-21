# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-072: Dataset ORM model — 9+1 durum makinesi.
# KR-073: AV1/AV2 rapor URI'leri.
"""Dataset SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class DatasetModel(Base):
    """datasets tablosu ORM modeli (KR-072, KR-073).

    Drone veri seti: 9 normal durum + 1 hata durumu (REJECTED_QUARANTINE).
    Manifest JSONB, SHA-256 hash, AV1/AV2 rapor URI'leri.
    """

    __tablename__ = "datasets"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.field_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'RAW_INGESTED'"))
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    av1_report_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    av2_report_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_calibrated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    worker_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    result_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarantine_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_bands: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)), nullable=False, server_default=text("'{}'::varchar[]")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
