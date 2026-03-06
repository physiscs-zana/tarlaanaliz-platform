# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Weather Block raporlama detay tabloları.

Amaç: SOP 2.4 ve KR-015-5 kapsamında hava durumu kanıtlarının saklanacağı
    weather_block_reports yapısını kurmak.
Sorumluluk: Uçuş iptallerinin belgelenmesi ve otomatik yeniden planlama desteği.
Bağımlılıklar: kr082 (calibration_qc_records) migration'ının tamamlanmış olması.
    missions, pilots tablolarının mevcut olması.

Revision ID: wbr001
Revises: kr082
Create Date: 2026-02-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "wbr001"
down_revision: Union[str, None] = "kr082"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # weather_block_reports tablosu
    # Hava koşulları nedeniyle iptal edilen uçuşların kanıt ve akış kaydı
    # -------------------------------------------------------------------------
    op.create_table(
        "weather_block_reports",
        sa.Column("weather_block_report_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pilot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            sa.CheckConstraint(
                "status IN ('REPORTED', 'VERIFIED', 'RESOLVED', 'REJECTED')",
                name="ck_wbr_status",
            ),
            nullable=False,
            server_default="REPORTED",
        ),
        # Hava koşulu: rain, wind, cloud, fog, vb.
        sa.Column("weather_condition", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        # Kanıt dosyaları (fotoğraf, ekran görüntüsü)
        sa.Column("evidence_blob_ids", sa.dialects.postgresql.JSONB, nullable=True),
        # Admin doğrulama
        sa.Column(
            "verified_by_admin_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        # Otomatik yeniden planlama
        sa.Column(
            "auto_rescheduled_mission_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reschedule_token_consumed", sa.Boolean, server_default=sa.text("false"), nullable=False),
        # Zaman damgaları
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("weather_block_reports")
