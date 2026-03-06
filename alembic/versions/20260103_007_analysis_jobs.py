# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Analysis jobs schema.

KR-017 (YZ Izolasyonu) ve KR-081.1 (Job Schema) geregi analysis_jobs
tablosunu olusturmak. Is durumunu (QUEUED, PROCESSING, COMPLETED) takip etmek.

Revision ID: 007
Revises: 006
Create Date: 2026-01-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Job status enum --
    job_status_enum = postgresql.ENUM(
        "QUEUED",
        "CALIBRATION_PENDING",
        "QC_PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="job_status",
        create_type=True,
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)

    # -- QC status enum (KR-018/KR-082) --
    qc_status_enum = postgresql.ENUM(
        "PASS",
        "WARN",
        "FAIL",
        name="qc_status",
        create_type=True,
    )
    qc_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Analysis jobs tablosu (KR-017: PII tasimaz, KR-081.1) --
    op.create_table(
        "analysis_jobs",
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.field_id"),
            nullable=False,
        ),
        sa.Column(
            "crop_type",
            postgresql.ENUM(
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
        ),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=True, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "QUEUED",
                "CALIBRATION_PENDING",
                "QC_PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="job_status",
                create_type=False,
            ),
            nullable=False,
            server_default="QUEUED",
        ),
        # KR-018/KR-082: kalibrasyon hard gate
        sa.Column("requires_calibrated", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_calibrated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Model bilgileri
        sa.Column("model_id", sa.String(100), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        # Job zamanlamalari
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        # Input/Output referanslari (S3 paths, PII yok)
        sa.Column("input_manifest", postgresql.JSONB(), nullable=True),
        sa.Column("output_manifest", postgresql.JSONB(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_analysis_jobs_mission", "analysis_jobs", ["mission_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status", "queued_at"])
    op.create_index("ix_analysis_jobs_field", "analysis_jobs", ["field_id"])

    # -- Analysis results tablosu (KR-081.2) --
    op.create_table(
        "analysis_results",
        sa.Column(
            "result_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column("overall_health_index", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("findings", postgresql.JSONB(), nullable=True),
        sa.Column("summary_notes", sa.Text(), nullable=True),
        sa.Column("layer_refs", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("result_hash_sha256", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_analysis_results_job", "analysis_results", ["job_id"])
    op.create_index("ix_analysis_results_mission", "analysis_results", ["mission_id"])


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")

    op.execute("DROP TYPE IF EXISTS qc_status")
    op.execute("DROP TYPE IF EXISTS job_status")
