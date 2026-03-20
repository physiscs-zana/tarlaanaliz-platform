# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-022: Immutable price snapshot ORM model.
# PATH: src/infrastructure/persistence/sqlalchemy/models/price_snapshot_model.py
# DESC: price_snapshots ORM modeli — fiyat anlık görüntüsü (değiştirilemez).
"""PriceSnapshot SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class PriceSnapshotModel(Base):
    __tablename__ = "price_snapshots"

    price_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
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
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_price_kurus: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'TRY'"))
    discount_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
