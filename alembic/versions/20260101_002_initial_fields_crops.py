# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Initial fields and crops schema.

KR-013 (Ciftci ve Tarla Yonetimi) geregi fields ve crops tablolarini
olusturmak. Il/Ilce/Ada/Parsel tekillik (unique) kisitlamasini uygulamak.

Revision ID: 002
Revises: 001
Create Date: 2026-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    from geoalchemy2 import Geometry
except ImportError:
    # geoalchemy2 su an devre disi (numpy CPU uyumsuzlugu).
    # Bu migration zaten uygulanmis; Alembic sadece revision haritasi icin parse ediyor.
    Geometry = None  # type: ignore[assignment,misc]

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- PostGIS extension --
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # -- Crop type enum (KR-024 bitki turleri) --
    crop_type_enum = postgresql.ENUM(
        "PAMUK",
        "ANTEP_FISTIGI",
        "MISIR",
        "BUGDAY",
        "AYCICEGI",
        "UZUM",
        "ZEYTIN",
        "KIRMIZI_MERCIMEK",
        name="crop_type",
        create_type=True,
    )
    crop_type_enum.create(op.get_bind(), checkfirst=True)

    # -- Fields tablosu (KR-013: tarla kaydi) --
    op.create_table(
        "fields",
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "coop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cooperatives.coop_id"),
            nullable=True,
        ),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("village", sa.String(100), nullable=False),
        sa.Column("block_no", sa.String(50), nullable=False),
        sa.Column("parcel_no", sa.String(50), nullable=False),
        sa.Column("area_m2", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("area_donum", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("boundary", Geometry("POLYGON", srid=4326), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # KR-013: Tekil kayit kurali — ayni parsel iki kez kaydedilemez
        sa.UniqueConstraint(
            "province",
            "district",
            "village",
            "block_no",
            "parcel_no",
            name="uq_fields_parcel",
        ),
    )
    op.create_index("ix_fields_user_id", "fields", ["user_id"])
    op.create_index("ix_fields_coop_id", "fields", ["coop_id"])

    # -- Field crops tablosu (tarla-bitki iliskisi, sezon bazli) --
    op.create_table(
        "field_crops",
        sa.Column(
            "field_crop_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.field_id", ondelete="CASCADE"),
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
        sa.Column("area_m2", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("season_year", sa.Integer(), nullable=False),
        # KR-013: Bitki turu degistirme — yilda 1, 1 Ekim - 31 Aralik arasi
        sa.Column("crop_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("field_id", "crop_type", "season_year", name="uq_field_crops_field_crop_season"),
    )
    op.create_index("ix_field_crops_field_id", "field_crops", ["field_id"])

    # -- Price snapshots tablosu (KR-022: immutable fiyat) --
    op.create_table(
        "price_snapshots",
        sa.Column(
            "price_snapshot_id",
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
        ),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column("unit_price_kurus", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="TRY"),
        sa.Column("discount_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("snapshot_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_price_snapshots_crop_type", "price_snapshots", ["crop_type", "effective_from"])


def downgrade() -> None:
    op.drop_table("price_snapshots")
    op.drop_table("field_crops")
    op.drop_table("fields")

    op.execute("DROP TYPE IF EXISTS crop_type")
    op.execute("DROP EXTENSION IF EXISTS postgis")
