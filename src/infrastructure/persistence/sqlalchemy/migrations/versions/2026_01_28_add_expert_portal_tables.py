# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

"""add expert portal tables

Revision ID: 2026_01_28_add_expert_portal_tables
Revises: 2026_01_27_add_v2_6_0_tables
Create Date: 2026-01-28

KR-019: Expert portal — experts, expert_reviews tablolari.
KR-029: Training feedback icin verdict + training_grade alanlari.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "2026_01_28_add_expert_portal_tables"
down_revision = "2026_01_27_add_v2_6_0_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- experts tablosu (KR-019) ---
    op.create_table(
        "experts",
        sa.Column(
            "expert_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("max_daily_quota", sa.Integer(), nullable=False),
        sa.Column(
            "specialization",
            postgresql.ARRAY(sa.String(length=50)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_by_admin_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("expert_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_admin_user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="uq_experts_user_id"),
    )
    op.create_index("ix_experts_province", "experts", ["province"])
    op.create_index("ix_experts_status", "experts", ["status"])

    # --- expert_reviews tablosu (KR-019, KR-029) ---
    op.create_table(
        "expert_reviews",
        sa.Column(
            "review_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verdict", sa.String(length=32), nullable=True),
        sa.Column("training_grade", sa.String(length=10), nullable=True),
        sa.Column("grade_reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("review_id"),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.mission_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expert_id"], ["experts.expert_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_expert_reviews_expert_id", "expert_reviews", ["expert_id"])
    op.create_index("ix_expert_reviews_mission_id", "expert_reviews", ["mission_id"])
    op.create_index("ix_expert_reviews_status", "expert_reviews", ["status"])

    # --- analysis_results tablosu (KR-081, KR-025) ---
    op.create_table(
        "analysis_results",
        sa.Column(
            "result_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("analysis_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_health_index", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("findings", postgresql.JSONB(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("report_tier", sa.String(length=32), nullable=False, server_default=sa.text("'TEMEL'")),
        sa.Column("band_class", sa.String(length=32), nullable=False, server_default=sa.text("''")),
        sa.Column(
            "available_layers",
            postgresql.ARRAY(sa.String(length=50)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("thermal_summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("result_id"),
        sa.UniqueConstraint("analysis_job_id", name="uq_analysis_results_job_id"),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.mission_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.field_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_analysis_results_mission_id", "analysis_results", ["mission_id"])
    op.create_index("ix_analysis_results_field_id", "analysis_results", ["field_id"])

    # --- audit_logs tablosu (BOLUM 3, KR-062) ---
    op.create_table(
        "audit_logs",
        sa.Column(
            "audit_log_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_action", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id_hash", sa.String(length=128), nullable=False),
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("card_id", sa.String(length=100), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_details", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.String(length=120), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    op.create_index("ix_audit_logs_actor_id_hash", "audit_logs", ["actor_id_hash"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])

    # --- datasets tablosu (KR-072) ---
    op.create_table(
        "datasets",
        sa.Column(
            "dataset_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'RAW_INGESTED'")),
        sa.Column("sha256_hash", sa.String(length=64), nullable=True),
        sa.Column("manifest", postgresql.JSONB(), nullable=True),
        sa.Column("av1_report_uri", sa.String(length=500), nullable=True),
        sa.Column("av2_report_uri", sa.String(length=500), nullable=True),
        sa.Column("is_calibrated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("worker_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_uri", sa.String(length=500), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column(
            "available_bands",
            postgresql.ARRAY(sa.String(length=20)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("dataset_id"),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.mission_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.field_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_datasets_mission_id", "datasets", ["mission_id"])
    op.create_index("ix_datasets_status", "datasets", ["status"])


def downgrade() -> None:
    op.drop_table("datasets")
    op.drop_table("audit_logs")
    op.drop_table("analysis_results")
    op.drop_table("expert_reviews")
    op.drop_table("experts")
