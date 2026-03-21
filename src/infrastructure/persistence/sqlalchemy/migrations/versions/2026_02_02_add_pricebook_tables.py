# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

"""add pricebook tables

Revision ID: 2026_02_02_add_pricebook_tables
Revises: 2026_01_26_add_expert_portal_tables
Create Date: 2026-02-02

KR-022: PriceBook fiyat yonetimi — pricebook_entries tablosu.
KR-022: Versiyonlu + tarih aralikli fiyat yonetimi.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "2026_02_02_add_pricebook_tables"
down_revision = "2026_01_28_add_expert_portal_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- pricebook_entries: Fiyat tanimlari (KR-022) ---
    op.create_table(
        "pricebook_entries",
        sa.Column(
            "entry_id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
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
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column("unit_price_kurus", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'TRY'")),
        sa.Column("discount_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("entry_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_pricebook_entries_crop_type", "pricebook_entries", ["crop_type"])
    op.create_index("ix_pricebook_entries_effective_from", "pricebook_entries", ["effective_from"])
    op.create_index(
        "ix_pricebook_entries_active_lookup",
        "pricebook_entries",
        ["crop_type", "analysis_type", "effective_from"],
    )


def downgrade() -> None:
    op.drop_table("pricebook_entries")
