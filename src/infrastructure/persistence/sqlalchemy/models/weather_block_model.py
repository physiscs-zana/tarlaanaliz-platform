# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: Weather block ORM model — hava engeli (force majeure) kayıtları.
"""WeatherBlock and WeatherBlockReport SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class WeatherBlockModel(Base):
    """weather_blocks tablosu ORM modeli (KR-015-5).

    Pilotların hava engeli bildirimlerini ve durumlarını saklar.
    Force majeure: reschedule token tüketmez.
    """

    __tablename__ = "weather_blocks"

    weather_block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id"), nullable=False, index=True
    )
    pilot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pilots.pilot_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        ENUM("PENDING", "VERIFIED", "REJECTED", name="weather_block_status", create_type=False),
        nullable=False,
        server_default="PENDING",
    )
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    blocked_date: Mapped[date] = mapped_column(Date(), nullable=False)
    evidence_blob_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_rescheduled: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, server_default=text("false")
    )
    rescheduled_mission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class WeatherBlockReportModel(Base):
    """weather_block_reports tablosu ORM modeli (KR-015-5, SOP 2.4).

    Hava koşulları nedeniyle iptal edilen uçuşların kanıt ve akış kaydı.
    """

    __tablename__ = "weather_block_reports"

    weather_block_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    pilot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pilots.pilot_id", ondelete="SET NULL"), nullable=True
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="REPORTED")
    weather_condition: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    evidence_blob_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verified_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_rescheduled_mission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="SET NULL"), nullable=True
    )
    reschedule_token_consumed: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
