# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015 (optional): mission_segments table (scaffold)

Rename file with real timestamp prefix per your convention.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "kr015a_mission_segments"
down_revision = "wbr001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mission_segments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("segment_no", sa.Integer(), nullable=False),
        sa.Column("area_donum", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_pilot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            sa.CheckConstraint(
                "status IN ('PLANNED','ASSIGNED','FLOWN','CANCELLED')",
                name="ck_mission_segment_status",
            ),
            nullable=False,
            server_default="PLANNED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_mission_segments_mission_id", "mission_segments", ["mission_id"])


def downgrade() -> None:
    op.drop_index("ix_mission_segments_mission_id", table_name="mission_segments")
    op.drop_table("mission_segments")
