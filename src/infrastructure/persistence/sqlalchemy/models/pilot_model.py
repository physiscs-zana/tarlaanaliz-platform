# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Pilot ORM model — capacity, work_days, reliability, service areas.
"""Pilot SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.sqlalchemy.base import Base


class PilotModel(Base):
    __tablename__ = "pilots"

    pilot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    drone_model: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("''"))
    drone_serial_no: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    work_days: Mapped[list[str]] = mapped_column(
        ARRAY(String(3)), nullable=False, server_default=text("'{}'::varchar[]")
    )
    daily_capacity_donum: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("2750"))
    system_seed_quota: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1500"))
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default=text("1.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], lazy="selectin")
    service_areas = relationship("PilotServiceAreaModel", back_populates="pilot", cascade="all, delete-orphan")


class PilotServiceAreaModel(Base):
    __tablename__ = "pilot_service_areas"

    service_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    pilot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pilots.pilot_id", ondelete="CASCADE"), nullable=False
    )
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    pilot = relationship("PilotModel", back_populates="service_areas")


class MissionAssignmentModel(Base):
    __tablename__ = "mission_assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    pilot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pilots.pilot_id"), nullable=False)
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'SYSTEM_SEED'"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    override_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
