# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015: seasonal reschedule tokens + reschedule requests (scaffold)

Rename file with real timestamp prefix per your convention.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "kr015b_reschedule"
down_revision = "kr015a_mission_segments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # subscriptions token fields
    # Not: reschedule_tokens_remaining migration 004'te zaten eklendi; burada tekrar eklenmez.
    op.add_column("subscriptions", sa.Column("plan_type", sa.String(length=32), nullable=True))
    op.add_column("subscriptions", sa.Column("reschedule_tokens_per_season", sa.Integer(), nullable=True))

    # reschedule request table
    op.create_table(
        "subscription_reschedule_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column("occurrence_ref", sa.String(length=64), nullable=True),
        sa.Column("requested_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            sa.CheckConstraint(
                "status IN ('REQUESTED','APPROVED','REJECTED','CANCELED')",
                name="ck_reschedule_request_status",
            ),
            nullable=False,
            server_default="REQUESTED",
        ),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("subscription_id", "occurrence_ref", name="uq_reschedule_subscription_occurrence"),
    )


def downgrade() -> None:
    op.drop_table("subscription_reschedule_requests")
    op.drop_column("subscriptions", "reschedule_tokens_per_season")
    op.drop_column("subscriptions", "plan_type")
