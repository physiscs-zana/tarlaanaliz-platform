# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-014: Davet kodlari icin coop_invites tablosu.
"""Create coop_invites table for cooperative invite code management.

Revision ID: coop_invites
Revises: extend_pi_status
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "coop_invites"
down_revision: Union[str, None] = "extend_pi_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coop_invites",
        sa.Column(
            "invite_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "coop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cooperatives.coop_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invite_code", sa.String(6), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_coop_invites_code", "coop_invites", ["invite_code"])


def downgrade() -> None:
    op.drop_index("ix_coop_invites_code", table_name="coop_invites")
    op.drop_table("coop_invites")
