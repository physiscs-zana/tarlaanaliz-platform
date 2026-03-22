# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-083: İl Operatörü kar payı ORM modeli — aylık gelir payı hesaplama.
"""IlOperatorProfitShare SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class IlOperatorProfitShareModel(Base):
    """il_operator_profit_shares tablosu (KR-083).

    İl Operatörü aylık kar payı kaydı.
    Kar payı oranı: %5-%15 (admin tanımlı).
    Ödeme: ayın ilk 7 günü, Merkez Yönetim nihai onay sonrası.
    """

    __tablename__ = "il_operator_profit_shares"

    profit_share_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    operator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    period_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # "2026-04" formatı
    # Gelir ve pay hesabı
    total_revenue_kurus: Mapped[int] = mapped_column(Integer, nullable=False)
    share_percent: Mapped[int] = mapped_column(Integer, nullable=False)  # 5-15 arası (%)
    share_amount_kurus: Mapped[int] = mapped_column(Integer, nullable=False)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="CALCULATED"
    )  # CALCULATED → APPROVED → PAID
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
