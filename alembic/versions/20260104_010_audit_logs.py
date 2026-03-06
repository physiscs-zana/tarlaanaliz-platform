# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Audit logs schema (WORM - Write-Once-Read-Many).

BOLUM 3 (Gozlemlenebilirlik) ve KR-066 geregi degistirilemez audit_logs
tablosunu olusturmak. Update/Delete izni olmayan append-only yapi.

Revision ID: 010
Revises: 009
Create Date: 2026-01-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Event type enum (BOLUM 3 log semasi) --
    event_type_enum = postgresql.ENUM(
        "INGEST",
        "AUTH",
        "RBAC",
        "PRICING",
        "JOB",
        "RESULT",
        "SECURITY",
        "SYSTEM",
        "PAYMENT",
        "EXPERT",
        "MISSION",
        name="audit_event_type",
        create_type=True,
    )
    event_type_enum.create(op.get_bind(), checkfirst=True)

    # -- Event action enum --
    event_action_enum = postgresql.ENUM(
        "CREATE",
        "VALIDATE",
        "UPLOAD",
        "QUEUE",
        "START",
        "FINISH",
        "DENY",
        "UPDATE",
        "DELETE",
        "ASSIGN",
        "UNASSIGN",
        "QUARANTINE",
        "RELEASE",
        "CANCEL",
        "APPROVE",
        "REJECT",
        "REFUND",
        "ROLE_ASSIGN",
        "ROLE_REVOKE",
        "INTENT_CREATED",
        "MARK_PAID",
        "WEBHOOK_PAID",
        "EXPIRED",
        name="audit_event_action",
        create_type=True,
    )
    event_action_enum.create(op.get_bind(), checkfirst=True)

    # -- Audit logs tablosu (WORM: append-only) --
    op.create_table(
        "audit_logs",
        sa.Column(
            "log_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("service", sa.String(50), nullable=False),
        sa.Column("env", sa.String(10), nullable=False, server_default="prod"),
        sa.Column("app_version", sa.String(20), nullable=True),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                "INGEST",
                "AUTH",
                "RBAC",
                "PRICING",
                "JOB",
                "RESULT",
                "SECURITY",
                "SYSTEM",
                "PAYMENT",
                "EXPERT",
                "MISSION",
                name="audit_event_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "event_action",
            postgresql.ENUM(
                "CREATE",
                "VALIDATE",
                "UPLOAD",
                "QUEUE",
                "START",
                "FINISH",
                "DENY",
                "UPDATE",
                "DELETE",
                "ASSIGN",
                "UNASSIGN",
                "QUARANTINE",
                "RELEASE",
                "CANCEL",
                "APPROVE",
                "REJECT",
                "REFUND",
                "ROLE_ASSIGN",
                "ROLE_REVOKE",
                "INTENT_CREATED",
                "MARK_PAID",
                "WEBHOOK_PAID",
                "EXPIRED",
                name="audit_event_action",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(10), nullable=False),
        # Correlation / tracing (BOLUM 3: her zaman zorunlu)
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("span_id", sa.String(32), nullable=True),
        # Actor bilgileri (PII yok — hash/opaque ID)
        sa.Column("actor_type", sa.String(30), nullable=True),
        sa.Column("actor_id_hash", sa.String(128), nullable=True),
        sa.Column("device_id", sa.String(100), nullable=True),
        # Referans ID'leri
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("batch_id", sa.String(100), nullable=True),
        sa.Column("card_id", sa.String(100), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        # HTTP bilgileri (opsiyonel)
        sa.Column("http_method", sa.String(10), nullable=True),
        sa.Column("http_path", sa.String(255), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        # Hata bilgileri
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(120), nullable=True),
        # Detay payload (PII icermez)
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("pii", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_audit_logs_ts", "audit_logs", [sa.text("ts DESC")])
    op.create_index("ix_audit_logs_correlation", "audit_logs", ["correlation_id"])
    op.create_index("ix_audit_logs_event", "audit_logs", ["event_type", "event_action"])
    op.create_index("ix_audit_logs_mission", "audit_logs", ["mission_id"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor_id_hash", sa.text("ts DESC")])

    # -- WORM: Prevent UPDATE and DELETE on audit_logs --
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_audit_logs_immutable()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only (WORM). UPDATE and DELETE are not allowed.';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION fn_audit_logs_immutable();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION fn_audit_logs_immutable();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_no_delete ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS fn_audit_logs_immutable()")

    op.drop_table("audit_logs")

    op.execute("DROP TYPE IF EXISTS audit_event_action")
    op.execute("DROP TYPE IF EXISTS audit_event_type")
