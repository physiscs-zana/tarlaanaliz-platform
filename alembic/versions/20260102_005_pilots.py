# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Pilots and capacity schema.

KR-015-1 (Pilot Kapasite) ve KR-031 (Hakedis) geregi pilots ve
capacity tablolarini olusturmak.

Revision ID: 005
Revises: 004
Create Date: 2026-01-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Pilots tablosu (KR-015) --
    op.create_table(
        "pilots",
        sa.Column(
            "pilot_id",
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
        sa.Column("drone_model", sa.String(100), nullable=False, server_default="DJI Mavic 3M"),
        sa.Column("drone_serial_no", sa.String(100), nullable=False, unique=True),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        # KR-015-1: calisma gunleri (bitfield veya array)
        sa.Column(
            "work_days",
            postgresql.ARRAY(sa.String(3)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        # KR-015-1: gunluk kapasite (2500-3000 donum/gun, varsayilan 2750)
        sa.Column(
            "daily_capacity_donum",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2750"),
        ),
        # KR-015-2: sistem tarafindan verilen kota (varsayilan 1500)
        sa.Column(
            "system_seed_quota",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1500"),
        ),
        sa.Column("reliability_score", sa.Numeric(precision=4, scale=2), nullable=False, server_default=sa.text("1.00")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "daily_capacity_donum >= 2500 AND daily_capacity_donum <= 3000",
            name="ck_pilots_capacity_range",
        ),
        sa.CheckConstraint(
            "array_length(work_days, 1) IS NULL OR array_length(work_days, 1) <= 6",
            name="ck_pilots_work_days_max",
        ),
    )

    # -- Pilot service areas (hizmet verdigi mahalle/koy listesi) --
    op.create_table(
        "pilot_service_areas",
        sa.Column(
            "service_area_id",
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
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("village", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_pilot_service_areas_pilot_id", "pilot_service_areas", ["pilot_id"])

    # -- Mission pilot atamalari --
    op.create_table(
        "mission_assignments",
        sa.Column(
            "assignment_id",
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
            "pilot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pilots.pilot_id"),
            nullable=False,
        ),
        sa.Column("assignment_type", sa.String(20), nullable=False, server_default="SYSTEM_SEED"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        # KR-015-4: admin override alanlari
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column(
            "overridden_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=True,
        ),
    )
    op.create_index("ix_mission_assignments_mission", "mission_assignments", ["mission_id"])
    op.create_index("ix_mission_assignments_pilot", "mission_assignments", ["pilot_id", "is_current"])

    # -- Pilot hakedis tablosu (KR-031) --
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
            sa.ForeignKey("pilots.pilot_id"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id"),
            nullable=False,
        ),
        sa.Column("area_donum", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("rate_kurus_per_donum", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("total_kurus", sa.BigInteger(), nullable=False),
        sa.Column("coverage_ratio", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("pilot_id", "mission_id", name="uq_pilot_earnings_pilot_mission"),
    )
    op.create_index("ix_pilot_earnings_period", "pilot_earnings", ["pilot_id", "period_month"])

    # -- CropOpsProfile tablosu (KR-015-1: bitki bazli kapasite profili) --
    op.create_table(
        "crop_ops_profiles",
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
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
            unique=True,
        ),
        sa.Column("daily_capacity_donum", sa.Integer(), nullable=False, server_default=sa.text("2750")),
        sa.Column("system_seed_quota", sa.Integer(), nullable=False, server_default=sa.text("1500")),
        sa.Column("recommended_interval_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("crop_ops_profiles")
    op.drop_table("pilot_earnings")
    op.drop_table("mission_assignments")
    op.drop_table("pilot_service_areas")
    op.drop_table("pilots")
