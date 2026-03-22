# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-031, KR-083, KR-012: Pilot hakediş, İl Operatör kar payı, duyuru tabloları.
"""Pilot earnings, IL operator profit share, announcements tables.

Revision ID: kr031_083_012
Revises: gist_001
Create Date: 2026-03-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "kr031_083_012"
down_revision: Union[str, None] = "gist_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # KR-031: pilot_rates_by_province — il bazında pilot birim ücret
    # ---------------------------------------------------------------
    op.create_table(
        "pilot_rates_by_province",
        sa.Column(
            "rate_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("province", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "rate_per_donum_kurus",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("300"),
        ),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ---------------------------------------------------------------
    # KR-031: pilot_earnings — pilot aylık hakediş kaydı
    # ---------------------------------------------------------------
    op.create_table(
        "pilot_earnings",
        sa.Column(
            "earning_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "pilot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("area_donum", sa.Integer(), nullable=False),
        sa.Column("rate_per_donum_kurus", sa.Integer(), nullable=False),
        sa.Column("amount_kurus", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("dispute_reason", sa.Text(), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispute_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispute_resolution", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("pilot_id", "mission_id", name="uq_pilot_earning_mission"),
    )
    op.create_index("ix_pilot_earnings_pilot_id", "pilot_earnings", ["pilot_id"])
    op.create_index("ix_pilot_earnings_period", "pilot_earnings", ["period_month"])

    # ---------------------------------------------------------------
    # KR-083: il_operator_profit_shares — İl Operatör kar payı
    # ---------------------------------------------------------------
    op.create_table(
        "il_operator_profit_shares",
        sa.Column(
            "profit_share_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "operator_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("total_revenue_kurus", sa.Integer(), nullable=False),
        sa.Column("share_percent", sa.Integer(), nullable=False),
        sa.Column("share_amount_kurus", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="CALCULATED"),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_il_profit_operator", "il_operator_profit_shares", ["operator_user_id"])
    op.create_index("ix_il_profit_province_period", "il_operator_profit_shares", ["province", "period_month"])

    # ---------------------------------------------------------------
    # KR-012: announcements — duyuru/kampanya/uçuş başlangıç tarihi
    # ---------------------------------------------------------------
    op.create_table(
        "announcements",
        sa.Column(
            "announcement_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("announcement_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_roles", sa.String(200), nullable=True),
        sa.Column("target_province", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "visible_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_announcements_type_active", "announcements", ["announcement_type", "is_active"])


def downgrade() -> None:
    op.drop_table("announcements")
    op.drop_table("il_operator_profit_shares")
    op.drop_table("pilot_earnings")
    op.drop_table("pilot_rates_by_province")
