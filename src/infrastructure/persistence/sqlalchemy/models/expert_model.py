# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-019: Expert ORM model — curated onboarding, specialization, kota, bolge yetkisi.
"""Expert SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.sqlalchemy.base import Base


class ExpertModel(Base):
    """experts tablosu ORM modeli (KR-019).

    Uzman hesabi self-signup DEGILDIR: ADMIN kontrollu acilir.
    Uzman yalnizca kendisine atanmis incelemeleri gorur (ownership check).
    """

    __tablename__ = "experts"

    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    max_daily_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    specialization: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, server_default=text("'{}'::varchar[]")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'ACTIVE'"))
    created_by_admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], lazy="selectin")
