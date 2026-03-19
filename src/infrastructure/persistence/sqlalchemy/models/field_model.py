# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-013: Field ORM model — parcel registration and geometry.
"""Field SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class FieldModel(Base):
    __tablename__ = "fields"
    __table_args__ = (
        UniqueConstraint("province", "district", "village", "block_no", "parcel_no", name="uq_field_parcel"),
    )

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    coop_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str] = mapped_column(String(100), nullable=False)
    block_no: Mapped[str] = mapped_column(String(50), nullable=False)
    parcel_no: Mapped[str] = mapped_column(String(50), nullable=False)
    area_m2: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area_donum: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    crop_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        unique=True,
        server_default=text("LPAD(nextval('field_code_seq')::text, 8, '0')"),
        comment="8-digit human-readable field code for payment flows",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
