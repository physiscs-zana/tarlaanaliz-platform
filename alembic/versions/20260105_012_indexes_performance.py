# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Performance indexes for query optimization.
"""Veritabani performans optimizasyonu icin B-Tree indeksleri.

Revision ID: 012
Revises: 011
Create Date: 2026-01-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """Check if a table exists in the current database — no transaction damage."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_schema = 'public' AND table_name = :t"
            ")"
        ),
        {"t": table_name},
    )
    return result.scalar() is True


def _index_exists(index_name: str) -> bool:
    """Check if an index already exists."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM pg_indexes"
            "  WHERE indexname = :idx"
            ")"
        ),
        {"idx": index_name},
    )
    return result.scalar() is True


def _create_index(name: str, table: str, columns: list, **kw) -> None:
    """Create index only if table exists and index doesn't already exist."""
    if not _table_exists(table):
        print(f"  SKIP: {name} — table '{table}' does not exist yet")
        return
    if _index_exists(name):
        print(f"  SKIP: {name} — index already exists")
        return
    op.create_index(name, table, columns, **kw)


def upgrade() -> None:
    # missions (created in 003)
    _create_index("idx_missions_status_due", "missions", ["status", "due_at"], unique=False)
    _create_index("idx_missions_field_created", "missions", ["field_id", sa.text("created_at DESC")], unique=False)
    _create_index("idx_missions_subscription", "missions", ["subscription_id", sa.text("created_at DESC")], unique=False)
    _create_index("idx_missions_payment_intent", "missions", ["payment_intent_id"], unique=False)

    # mission_assignments (created in 005)
    _create_index("idx_mission_assignments_status", "mission_assignments", ["pilot_id", "is_current"], unique=False)

    # subscriptions (created in 004)
    _create_index("idx_subscriptions_due", "subscriptions", ["status", "next_due_at"], unique=False)
    _create_index("idx_subscriptions_field", "subscriptions", ["field_id", "status"], unique=False)
    _create_index("idx_subscriptions_payment_intent", "subscriptions", ["payment_intent_id"], unique=False)

    # payment_intents (created in kr033 — may not exist on main branch yet)
    _create_index("idx_payment_intents_target", "payment_intents", ["target_type", "target_id"], unique=False)
    _create_index("idx_payment_intents_status", "payment_intents", ["status", sa.text("created_at DESC")], unique=False)
    _create_index("idx_payment_intents_payer", "payment_intents", ["payer_user_id", sa.text("created_at DESC")], unique=False)

    # analysis_jobs (created in 007)
    _create_index("idx_analysis_jobs_mission", "analysis_jobs", ["mission_id"], unique=False)
    _create_index("idx_analysis_jobs_status", "analysis_jobs", ["status", sa.text("created_at DESC")], unique=False)

    # analysis_results (created in 007)
    _create_index("idx_analysis_results_mission", "analysis_results", ["mission_id"], unique=False)
    _create_index("idx_analysis_results_job", "analysis_results", ["job_id"], unique=False)

    # expert_reviews (created in 008)
    _create_index("idx_expert_reviews_expert_status", "expert_reviews", ["expert_id", "status"], unique=False)
    _create_index("idx_expert_reviews_mission", "expert_reviews", ["mission_id"], unique=False)

    # audit_logs (created in 010)
    _create_index("idx_audit_logs_event_type", "audit_logs", ["event_type", sa.text("created_at DESC")], unique=False)
    _create_index("idx_audit_logs_actor", "audit_logs", ["actor_id_hash", sa.text("created_at DESC")], unique=False)
    _create_index("idx_audit_logs_correlation", "audit_logs", ["correlation_id"], unique=False)
    _create_index("idx_audit_logs_mission", "audit_logs", ["mission_id", sa.text("created_at DESC")], unique=False)

    # weather_block_reports (created in 009 or wbr001)
    _create_index("idx_weather_blocks_mission", "weather_block_reports", ["mission_id"], unique=False)
    _create_index("idx_weather_blocks_status", "weather_block_reports", ["status"], unique=False)

    # calibration_records (created in kr082)
    _create_index("idx_calibration_records_mission", "calibration_records", ["mission_id"], unique=False)

    # qc_reports (created in kr082)
    _create_index("idx_qc_reports_status", "qc_reports", ["status"], unique=False)

    # feedback_records (created in 008)
    _create_index("idx_feedback_grade", "feedback_records", ["training_grade", sa.text("created_at DESC")], unique=False)
    _create_index("idx_feedback_mission", "feedback_records", ["mission_id", sa.text("created_at DESC")], unique=False)

    # price_snapshots (created in kr033 or later)
    _create_index("idx_price_snapshots_crop_type", "price_snapshots", ["crop_type", "analysis_type", "effective_from"], unique=False)

    # fields (created in 002)
    _create_index("idx_fields_user", "fields", ["user_id", "is_active"], unique=False)
    _create_index("idx_fields_province_district", "fields", ["province", "district"], unique=False)

    # users (created in 001)
    _create_index("idx_users_province", "users", ["province"], unique=False)

    # pilots (created in 005)
    _create_index("idx_pilots_province_status", "pilots", ["province", "is_active"], unique=False)


def downgrade() -> None:
    # Safe drop — check existence before dropping
    all_indexes = [
        ("idx_pilots_province_status", "pilots"),
        ("idx_users_province", "users"),
        ("idx_fields_province_district", "fields"),
        ("idx_fields_user", "fields"),
        ("idx_price_snapshots_crop_type", "price_snapshots"),
        ("idx_feedback_mission", "feedback_records"),
        ("idx_feedback_grade", "feedback_records"),
        ("idx_qc_reports_status", "qc_reports"),
        ("idx_calibration_records_mission", "calibration_records"),
        ("idx_weather_blocks_status", "weather_block_reports"),
        ("idx_weather_blocks_mission", "weather_block_reports"),
        ("idx_audit_logs_mission", "audit_logs"),
        ("idx_audit_logs_correlation", "audit_logs"),
        ("idx_audit_logs_actor", "audit_logs"),
        ("idx_audit_logs_event_type", "audit_logs"),
        ("idx_expert_reviews_mission", "expert_reviews"),
        ("idx_expert_reviews_expert_status", "expert_reviews"),
        ("idx_analysis_results_job", "analysis_results"),
        ("idx_analysis_results_mission", "analysis_results"),
        ("idx_analysis_jobs_status", "analysis_jobs"),
        ("idx_analysis_jobs_mission", "analysis_jobs"),
        ("idx_payment_intents_payer", "payment_intents"),
        ("idx_payment_intents_status", "payment_intents"),
        ("idx_payment_intents_target", "payment_intents"),
        ("idx_subscriptions_payment_intent", "subscriptions"),
        ("idx_subscriptions_field", "subscriptions"),
        ("idx_subscriptions_due", "subscriptions"),
        ("idx_mission_assignments_status", "mission_assignments"),
        ("idx_missions_payment_intent", "missions"),
        ("idx_missions_subscription", "missions"),
        ("idx_missions_field_created", "missions"),
        ("idx_missions_status_due", "missions"),
    ]
    for name, table in all_indexes:
        if _table_exists(table) and _index_exists(name):
            op.drop_index(name, table_name=table)
