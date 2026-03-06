# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Experts and specializations schema.

KR-019 (Expert Portal) geregi experts tablosunu ve uzmanlik
alanlarini (specializations) tanimlamak.

Revision ID: 006
Revises: 005
Create Date: 2026-01-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Expert specialization enum --
    specialization_enum = postgresql.ENUM(
        "DISEASE",
        "PEST",
        "WEED",
        "WATER_STRESS",
        "N_STRESS",
        "FUNGUS",
        "GENERAL",
        name="expert_specialization",
        create_type=True,
    )
    specialization_enum.create(op.get_bind(), checkfirst=True)

    # -- Experts tablosu (KR-019: curated onboarding) --
    op.create_table(
        "experts",
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Onboarding admin tarafindan yapilir
        sa.Column(
            "onboarded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=True,
        ),
        sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("daily_review_quota", sa.Integer(), nullable=False, server_default=sa.text("20")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # -- Expert specializations (many-to-many) --
    op.create_table(
        "expert_specializations",
        sa.Column(
            "expert_spec_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experts.expert_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "specialization",
            postgresql.ENUM(
                "DISEASE",
                "PEST",
                "WEED",
                "WATER_STRESS",
                "N_STRESS",
                "FUNGUS",
                "GENERAL",
                name="expert_specialization",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("expert_id", "specialization", name="uq_expert_specializations"),
    )
    op.create_index("ix_expert_specializations_expert_id", "expert_specializations", ["expert_id"])

    # -- Expert zone authority (bolge yetkisi) --
    op.create_table(
        "expert_zone_authorities",
        sa.Column(
            "zone_authority_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experts.expert_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_expert_zone_authorities_expert_id", "expert_zone_authorities", ["expert_id"])


def downgrade() -> None:
    op.drop_table("expert_zone_authorities")
    op.drop_table("expert_specializations")
    op.drop_table("experts")

    op.execute("DROP TYPE IF EXISTS expert_specialization")
