# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-072: datasets tablosu — 9+1 durumlu chain-of-custody state machine.
"""Create datasets table for chain-of-custody (KR-072).

Revision ID: datasets_001
Revises: coop_invites
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "datasets_001"
down_revision: Union[str, None] = "coop_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.field_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'RAW_INGESTED'")),
        sa.Column("sha256_hash", sa.String(64), nullable=True),
        sa.Column("manifest", postgresql.JSONB, nullable=True),
        sa.Column("av1_report_uri", sa.String(500), nullable=True),
        sa.Column("av2_report_uri", sa.String(500), nullable=True),
        sa.Column("is_calibrated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("worker_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_uri", sa.String(500), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column(
            "available_bands",
            postgresql.ARRAY(sa.String(20)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_datasets_mission_id", "datasets", ["mission_id"])
    op.create_index("ix_datasets_field_id", "datasets", ["field_id"])
    op.create_index("ix_datasets_status", "datasets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_datasets_status", table_name="datasets")
    op.drop_index("ix_datasets_field_id", table_name="datasets")
    op.drop_index("ix_datasets_mission_id", table_name="datasets")
    op.drop_table("datasets")
