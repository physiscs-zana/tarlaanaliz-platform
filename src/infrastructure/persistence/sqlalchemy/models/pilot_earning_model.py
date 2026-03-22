# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-031: Pilot hakediş ORM modeli — aylık kazanç, il bazlı ücret, itiraz.
"""PilotEarning and PilotRateByProvince SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class PilotRateByProvinceModel(Base):
    """pilot_rates_by_province tablosu (KR-031).

    İl bazında pilot birim ücret tanımı. CENTRAL_ADMIN tarafından yönetilir.
    Tanımsız il'ler için varsayılan 3 TL/dönüm kullanılır.
    """

    __tablename__ = "pilot_rates_by_province"

    rate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    province: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    rate_per_donum_kurus: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("300")
    )  # 300 kuruş = 3 TL varsayılan
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class PilotEarningModel(Base):
    """pilot_earnings tablosu (KR-031).

    Pilot aylık hakediş kaydı. Onaylanan görevlerdeki taranan alan × birim fiyat.
    MissionID eşleşmeden hakediş oluşmaz (hard gate).
    """

    __tablename__ = "pilot_earnings"
    __table_args__ = (UniqueConstraint("pilot_id", "mission_id", name="uq_pilot_earning_mission"),)

    earning_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    pilot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pilots.pilot_id", ondelete="CASCADE"), nullable=False, index=True
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="RESTRICT"), nullable=False
    )
    period_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # "2026-04" formatı
    area_donum: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_per_donum_kurus: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_kurus: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    # Hakediş durumu
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="PENDING"
    )  # PENDING → APPROVED → PAID | DISPUTED → RESOLVED
    # İtiraz alanları (3 iş günü penceresi — KR-031)
    dispute_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    disputed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispute_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispute_resolution: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # Onay & ödeme
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
