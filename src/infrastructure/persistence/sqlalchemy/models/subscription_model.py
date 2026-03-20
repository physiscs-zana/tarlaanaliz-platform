# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/infrastructure/persistence/sqlalchemy/models/subscription_model.py
# DESC: Subscription ORM modeli; subscriptions tablosunu ve KR-015/KR-027 alanlarını tanımlar.
# SSOT: KR-027 (abonelik planlayici), KR-015-5 (tarama takvimi + reschedule token), KR-033 (odeme)
"""
SubscriptionModel — SQLAlchemy ORM modeli.

Alembic migration 004 (subscriptions tablosu) ve
xxxx_kr015_seasonal_reschedule_tokens (plan_type, reschedule_tokens_per_season) ile uyumludur.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class SubscriptionModel(Base):
    """subscriptions tablosu ORM modeli (KR-027, KR-015-5, KR-033)."""

    __tablename__ = "subscriptions"

    # --- Birincil anahtar ---
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --- Yabancı anahtarlar ---
    farmer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.field_id"),
        nullable=False,
        index=True,
    )
    price_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("price_snapshots.price_snapshot_id"),
        nullable=False,
    )
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # --- Temel alanlar (KR-027) ---
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
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # --- Durum (KR-027 kanonik abonelik durumlari) ---
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="PENDING_PAYMENT",
    )

    # --- KR-015-5: Reschedule token ---
    reschedule_tokens_remaining: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="2",
    )

    # --- KR-015: Plan turu ve token kotasi (migration xxxx_kr015_seasonal_reschedule_tokens) ---
    plan_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reschedule_tokens_per_season: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Zaman damgalari ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
