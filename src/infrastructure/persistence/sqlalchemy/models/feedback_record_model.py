# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-029: FeedbackRecord ORM model — YZ egitim geri bildirim kaydi.
"""FeedbackRecord SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class FeedbackRecordModel(Base):
    """feedback_records tablosu ORM modeli (KR-029, KR-019).

    Uzman geri bildirimlerini YZ egitim pipeline'ina aktarmak icin kullanilir.
    Verdict: confirmed | corrected | rejected | needs_more_expert.
    Training grade: A | B | C | D | REJECT.
    """

    __tablename__ = "feedback_records"

    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expert_reviews.review_id", ondelete="CASCADE"), nullable=False
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    training_grade: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    corrected_class: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expert_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    image_quality: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    no_conflict: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
