# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: Mission segment ORM model — büyük tarla bölümleme.
"""MissionSegment SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class MissionSegmentModel(Base):
    """mission_segments tablosu ORM modeli (KR-015).

    Büyük tarlaların segment'lere bölünerek farklı pilotlara
    atanabilmesini sağlar.
    """

    __tablename__ = "mission_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.mission_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_no: Mapped[int] = mapped_column(Integer, nullable=False)
    area_donum: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_pilot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pilots.pilot_id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="PLANNED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
