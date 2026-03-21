# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-018: CalibrationRecord ORM model — radyometrik kalibrasyon kaydi.
"""CalibrationRecord SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class CalibrationRecordModel(Base):
    """calibration_records tablosu ORM modeli (KR-018, KR-082).

    Radyometrik kalibrasyon kaydi.
    Status: PENDING | CALIBRATED | FAILED.
    """

    __tablename__ = "calibration_records"

    calibration_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'PENDING'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    calibration_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    processing_report_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    calibration_result_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    qc_report_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
