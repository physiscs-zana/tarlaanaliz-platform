# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-081: AnalysisResult ORM model — contract-first JSON Schema.
# KR-025: Analiz sonucu; YZ sadece analiz yapar, ilaclama karari VERMEZ.
"""AnalysisResult SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class AnalysisResultModel(Base):
    """analysis_results tablosu ORM modeli (KR-081, KR-025).

    YZ analiz sonucu: overall_health_index + findings + summary.
    KR-025: summary 'YZ analizidir; ilaclama karari vermez.' uyarisini icerir.
    KR-023: Katmanli rapor — TEMEL / GENISLETILMIS / KAPSAMLI.
    KR-084: Termal analiz sonuclari (opsiyonel).
    """

    __tablename__ = "analysis_results"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    analysis_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.mission_id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fields.field_id", ondelete="CASCADE"), nullable=False
    )
    overall_health_index: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    findings: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    report_tier: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'TEMEL'"))
    band_class: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("''"))
    available_layers: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, server_default=text("'{}'::varchar[]")
    )
    thermal_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
