# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-019: ExpertReview ORM model — uzman inceleme atama ve karar kaydi.
# KR-029: Training feedback icin verdict + training_grade.
"""ExpertReview SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.sqlalchemy.base import Base


class ExpertReviewModel(Base):
    """expert_reviews tablosu ORM modeli (KR-019, KR-029).

    Modelin dusuk guven verdigi veya celiskili durumlarda manuel inceleme.
    Verdict: confirmed | corrected | rejected | needs_more_expert.
    Training grade: A | B | C | D | REJECT.
    """

    __tablename__ = "expert_reviews"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experts.expert_id", ondelete="CASCADE"), nullable=False
    )
    analysis_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'PENDING'"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    training_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    grade_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    expert = relationship("ExpertModel", foreign_keys=[expert_id], lazy="selectin")
