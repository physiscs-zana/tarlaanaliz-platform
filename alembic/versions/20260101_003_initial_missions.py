# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Initial missions schema.

KR-028 (Mission Yasam Dongusu) geregi missions tablosunu ve status
enumlarini (PLANNED, FLOWN, DONE vb.) olusturmak.

Revision ID: 003
Revises: 002
Create Date: 2026-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Mission status enum (KR-028) --
    mission_status_enum = postgresql.ENUM(
        "PLANNED",
        "ASSIGNED",
        "ACKED",
        "FLOWN",
        "UPLOADED",
        "ANALYZING",
        "DONE",
        "FAILED",
        "CANCELLED",
        name="mission_status",
        create_type=True,
    )
    mission_status_enum.create(op.get_bind(), checkfirst=True)

    # -- Route file type enum --
    route_file_type_enum = postgresql.ENUM(
        "KML",
        "KMZ",
        "WPML",
        name="route_file_type",
        create_type=True,
    )
    route_file_type_enum.create(op.get_bind(), checkfirst=True)

    # -- Missions tablosu (KR-028 kanonik SQL'den) --
    op.create_table(
        "missions",
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.field_id"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "payment_intent_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
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
            "status",
            postgresql.ENUM(
                "PLANNED",
                "ASSIGNED",
                "ACKED",
                "FLOWN",
                "UPLOADED",
                "ANALYZING",
                "DONE",
                "FAILED",
                "CANCELLED",
                name="mission_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PLANNED",
        ),
        # SLA zaman damgalari
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("flown_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "price_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("price_snapshots.price_snapshot_id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_missions_status_due", "missions", ["status", "due_at"])
    op.create_index("ix_missions_field_created", "missions", ["field_id", sa.text("created_at DESC")])
    op.create_index("ix_missions_subscription", "missions", ["subscription_id", sa.text("created_at DESC")])
    op.create_index("ix_missions_payment_intent", "missions", ["payment_intent_id"])

    # -- Mission route files tablosu (KR-028 gorev dosyasi) --
    op.create_table(
        "mission_route_files",
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.mission_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("parcel_ref", sa.String(255), nullable=False),
        sa.Column(
            "route_file_type",
            postgresql.ENUM("KML", "KMZ", "WPML", name="route_file_type", create_type=False),
            nullable=False,
        ),
        sa.Column("route_file_version", sa.String(50), nullable=True),
        sa.Column("route_file_hash_sha256", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_route_files_parcel", "mission_route_files", ["parcel_ref"])


def downgrade() -> None:
    op.drop_table("mission_route_files")
    op.drop_table("missions")

    op.execute("DROP TYPE IF EXISTS route_file_type")
    op.execute("DROP TYPE IF EXISTS mission_status")
