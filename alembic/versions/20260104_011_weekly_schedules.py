# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Weekly schedules schema.

KR-015-4 (Planlama Motoru) ciktilarinin saklanacagi weekly_schedules
tablolarini olusturmak.

Revision ID: 011
Revises: 010
Create Date: 2026-01-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Schedule status enum --
    schedule_status_enum = postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
        name="schedule_status",
        create_type=True,
    )
    schedule_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Weekly schedules tablosu (KR-015-4) --
    op.create_table(
        "weekly_schedules",
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("week_end_date", sa.Date(), nullable=False),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "DRAFT",
                "PUBLISHED",
                "IN_PROGRESS",
                "COMPLETED",
                "CANCELLED",
                name="schedule_status",
                create_type=False,
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_missions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_area_donum", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("week_start_date", "province", name="uq_weekly_schedules_week_province"),
    )
    op.create_index("ix_weekly_schedules_week", "weekly_schedules", ["week_start_date", "status"])

    # -- Schedule entries (her gundeki gorevler) --
    op.create_table(
        "schedule_entries",
        sa.Column(
            "entry_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("weekly_schedules.schedule_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column(
            "pilot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id"),
            nullable=False,
        ),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("estimated_area_donum", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("slot_order", sa.Integer(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("schedule_id", "mission_id", name="uq_schedule_entries_schedule_mission"),
    )
    op.create_index("ix_schedule_entries_schedule", "schedule_entries", ["schedule_id"])
    op.create_index("ix_schedule_entries_pilot_date", "schedule_entries", ["pilot_id", "scheduled_date"])
    op.create_index("ix_schedule_entries_mission", "schedule_entries", ["mission_id"])

    # -- Reschedule log (KR-015-5: gun degistirme kaydi) --
    op.create_table(
        "reschedule_logs",
        sa.Column(
            "reschedule_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.subscription_id"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=True,
        ),
        sa.Column("original_date", sa.Date(), nullable=False),
        sa.Column("new_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("is_weather_block", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("token_consumed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column(
            "pilot_confirmed",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column("pilot_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_reschedule_logs_subscription", "reschedule_logs", ["subscription_id"])


def downgrade() -> None:
    op.drop_table("reschedule_logs")
    op.drop_table("schedule_entries")
    op.drop_table("weekly_schedules")

    op.execute("DROP TYPE IF EXISTS schedule_status")
