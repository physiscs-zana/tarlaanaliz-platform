# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Subscriptions schema.

KR-027 (Abonelik Planlayici) geregi subscriptions tablosunu olusturmak;
periyot ve fiyat snapshot iliskilerini kurmak.

Revision ID: 004
Revises: 003
Create Date: 2026-01-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Subscription status enum (KR-027) --
    sub_status_enum = postgresql.ENUM(
        "PENDING_PAYMENT",
        "ACTIVE",
        "PAUSED",
        "CANCELLED",
        name="subscription_status",
        create_type=True,
    )
    sub_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Subscriptions tablosu (KR-027 kanonik SQL'den) --
    op.create_table(
        "subscriptions",
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "farmer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
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
        sa.Column(
            "interval_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING_PAYMENT",
                "ACTIVE",
                "PAUSED",
                "CANCELLED",
                name="subscription_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING_PAYMENT",
        ),
        sa.Column(
            "price_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("price_snapshots.price_snapshot_id"),
            nullable=False,
        ),
        sa.Column(
            "payment_intent_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        # KR-015-5: reschedule token
        sa.Column(
            "reschedule_tokens_remaining",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("interval_days > 0", name="ck_subscriptions_interval_positive"),
    )
    op.create_index("ix_subscriptions_due", "subscriptions", ["status", "next_due_at"])
    op.create_index("ix_subscriptions_field", "subscriptions", ["field_id", "status"])
    op.create_index("ix_subscriptions_payment_intent", "subscriptions", ["payment_intent_id"])

    # -- missions.subscription_id FK ekleme (simdi subscriptions tablosu mevcut) --
    op.create_foreign_key(
        "fk_missions_subscription_id",
        "missions",
        "subscriptions",
        ["subscription_id"],
        ["subscription_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_missions_subscription_id", "missions", type_="foreignkey")
    op.drop_table("subscriptions")

    op.execute("DROP TYPE IF EXISTS subscription_status")
