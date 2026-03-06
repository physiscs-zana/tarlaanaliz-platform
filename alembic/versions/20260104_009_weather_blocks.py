# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Weather blocks schema.

KR-015-5 (Force Majeure) geregi pilotlarin hava engeli bildirimlerini
ve durumlarini (PENDING, VERIFIED) saklamak.

Revision ID: 009
Revises: 008
Create Date: 2026-01-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Weather block status enum --
    wb_status_enum = postgresql.ENUM(
        "PENDING",
        "VERIFIED",
        "REJECTED",
        name="weather_block_status",
        create_type=True,
    )
    wb_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Weather blocks tablosu (KR-015-5) --
    op.create_table(
        "weather_blocks",
        sa.Column(
            "weather_block_id",
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
            "pilot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("PENDING", "VERIFIED", "REJECTED", name="weather_block_status", create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("blocked_date", sa.Date(), nullable=False),
        sa.Column("evidence_blob_id", sa.String(255), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        # KR-015-5: hava engeli reschedule token tuketmez
        sa.Column("auto_rescheduled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rescheduled_mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.mission_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_weather_blocks_mission", "weather_blocks", ["mission_id"])
    op.create_index("ix_weather_blocks_pilot", "weather_blocks", ["pilot_id", "blocked_date"])
    op.create_index("ix_weather_blocks_status", "weather_blocks", ["status"])


def downgrade() -> None:
    op.drop_table("weather_blocks")

    op.execute("DROP TYPE IF EXISTS weather_block_status")
