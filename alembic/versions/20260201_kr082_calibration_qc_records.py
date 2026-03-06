# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-018/KR-082 Radyometrik Kalibrasyon Hard Gate tabloları.

Amaç: calibration_records ve qc_reports tablolarını oluşturmak.
    AnalysisJob tablosuna kalibrasyon referansı eklemek.
Sorumluluk: Kalibre edilmemiş verinin işlenmesini engelleyen hard gate altyapısı.
Güvenlik: Veri bütünlüğü ve model güvenilirliği için kritik.
    KR-018: Kalibre edilmemiş veri işlenmez.
Bağımlılıklar: kr033 (payment_intents) migration'ının tamamlanmış olması.
    missions, analysis_jobs tablolarının mevcut olması.

Revision ID: kr082
Revises: kr033
Create Date: 2026-02-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "kr082"
down_revision: Union[str, None] = "kr033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # calibration_records tablosu
    # Radyometrik kalibrasyon kanıtı — her mission için zorunlu (KR-018)
    # -------------------------------------------------------------------------
    op.create_table(
        "calibration_records",
        sa.Column("calibration_record_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("batch_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        # CalibrationManifest VO: dataset URI, report URI, QC bayrakları
        sa.Column("calibration_manifest", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            sa.CheckConstraint(
                "status IN ('PENDING', 'CALIBRATED', 'FAILED')",
                name="ck_calibration_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        # Object store URI referansları
        sa.Column("processing_report_uri", sa.Text, nullable=True),
        sa.Column("calibration_result_uri", sa.Text, nullable=True),
        sa.Column("qc_report_uri", sa.Text, nullable=True),
        # Zaman damgaları
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # -------------------------------------------------------------------------
    # qc_reports tablosu
    # Kalibrasyon sonrası kalite kontrol — hard gate kararı (PASS/WARN/FAIL)
    # -------------------------------------------------------------------------
    op.create_table(
        "qc_reports",
        sa.Column("qc_report_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "calibration_record_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calibration_records.calibration_record_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(10),
            sa.CheckConstraint(
                "status IN ('PASS', 'WARN', 'FAIL')",
                name="ck_qc_status",
            ),
            nullable=False,
        ),
        # QC bayrakları: blur, overexposure, missing_bands, vb.
        sa.Column("flags", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "recommended_action",
            sa.String(20),
            sa.CheckConstraint(
                "recommended_action IN ('PROCEED', 'REVIEW', 'RETRY')",
                name="ck_qc_action",
            ),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        # Zaman damgaları
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # -------------------------------------------------------------------------
    # analysis_jobs tablosuna kalibrasyon referansı ekle
    # KR-018: requires_calibrated=true ise calibration_record_id zorunlu
    # NOT: requires_calibrated kolonu migration 007'de CREATE TABLE sırasında
    # zaten tanımlandı; buraya yeniden eklenmez.
    # -------------------------------------------------------------------------
    op.add_column(
        "analysis_jobs",
        sa.Column(
            "calibration_record_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calibration_records.calibration_record_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # analysis_jobs FK sütununu kaldır
    # NOT: requires_calibrated migration 007'e ait; buradan kaldırılmaz.
    op.drop_column("analysis_jobs", "calibration_record_id")

    # Tabloları kaldır (ters sırada)
    op.drop_table("qc_reports")
    op.drop_table("calibration_records")
