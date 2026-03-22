# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-012: Duyuru/kampanya ORM modeli — uçuş başlangıç tarihi ve genel bildirimler.
"""Announcement SQLAlchemy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.sqlalchemy.base import Base


class AnnouncementModel(Base):
    """announcements tablosu (KR-012).

    CENTRAL_ADMIN tarafından oluşturulan duyurular.
    Çiftçi/pilot sayfalarında görünür. Türe göre filtrelenir.

    Announcement types:
    - FLIGHT_START: Uçuşların başlayacağı tarih (season_start_date içerir)
    - CAMPAIGN: Tanıtım kampanyası / indirim duyurusu
    - GENERAL: Genel bilgilendirme
    - MAINTENANCE: Sistem bakım duyurusu
    """

    __tablename__ = "announcements"

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    announcement_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # FLIGHT_START | CAMPAIGN | GENERAL | MAINTENANCE
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    # Hedef tarih (ör: uçuş başlangıcı, kampanya bitiş tarihi)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Hedef roller (boşsa herkese görünür)
    target_roles: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # Virgülle ayrılmış: "FARMER_SINGLE,FARMER_MEMBER,COOP_OWNER"
    # Hedef il (boşsa tüm iller)
    target_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Görünürlük
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    visible_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    visible_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Oluşturan
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
