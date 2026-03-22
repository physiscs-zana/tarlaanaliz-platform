# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-028: Mission ORM model — analysis task lifecycle.
"""Mission SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class MissionModel(Base):
    __tablename__ = "missions"

    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.field_id"), nullable=False)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    crop_type: Mapped[str] = mapped_column(
        ENUM(
            "PAMUK",
            "ANTEP_FISTIGI",
            "MISIR",
            "BUGDAY",
            "AYCICEGI",
            "UZUM",
            "ZEYTIN",
            "KIRMIZI_MERCIMEK",
            name="crop_type",
            create_type=False,
        ),
        nullable=False,
    )
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, default="MULTISPECTRAL")
    status: Mapped[str] = mapped_column(
        ENUM(
            "PLANNED",
            "ASSIGNED",
            "ACKED",
            "FLOWN",
            "UPLOADED",
            "ANALYZING",
            "DONE",
            "FAILED",
            "CANCELLED",
            name="mission_status",
            create_type=False,
        ),
        nullable=False,
        server_default=text("'PLANNED'"),
    )
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    flown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    price_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # KR-015: Sezonluk zamanlama penceresi ve atama meta verisi
    schedule_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schedule_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assignment_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assignment_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
