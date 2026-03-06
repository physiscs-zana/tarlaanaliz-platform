# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Initial users and roles schema.

KR-063 (RBAC Yetki Matrisi) ve KR-050 (Auth Model - Telefon+PIN) geregi
users ve roles tablolarini olusturmak.

Revision ID: 001
Revises: None
Create Date: 2026-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Role enum (KR-063: 12 kanonik rol) --
    role_enum = postgresql.ENUM(
        "FARMER_SINGLE",
        "FARMER_MEMBER",
        "COOP_OWNER",
        "COOP_ADMIN",
        "COOP_AGRONOMIST",
        "COOP_VIEWER",
        "PILOT",
        "STATION_OPERATOR",
        "IL_OPERATOR",
        "CENTRAL_ADMIN",
        "AI_SERVICE",
        "EXPERT",
        name="user_role",
        create_type=True,
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    # -- Users tablosu (KR-050: telefon + 6-haneli PIN) --
    op.create_table(
        "users",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("pin_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("must_change_pin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # -- Roles tablosu (kullanici-rol iliskisi, coklu rol destegi) --
    op.create_table(
        "user_roles",
        sa.Column(
            "user_role_id",
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
            "role",
            postgresql.ENUM(
                "FARMER_SINGLE",
                "FARMER_MEMBER",
                "COOP_OWNER",
                "COOP_ADMIN",
                "COOP_AGRONOMIST",
                "COOP_VIEWER",
                "PILOT",
                "STATION_OPERATOR",
                "IL_OPERATOR",
                "CENTRAL_ADMIN",
                "AI_SERVICE",
                "EXPERT",
                name="user_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    # -- Kooperatif / Uretici Birligi tablosu (KR-014) --
    coop_status_enum = postgresql.ENUM(
        "PENDING_APPROVAL",
        "ACTIVE",
        "SUSPENDED",
        name="coop_status",
        create_type=True,
    )
    coop_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "cooperatives",
        sa.Column(
            "coop_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("PENDING_APPROVAL", "ACTIVE", "SUSPENDED", name="coop_status", create_type=False),
            nullable=False,
            server_default="PENDING_APPROVAL",
        ),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # -- Kooperatif uyelik tablosu --
    op.create_table(
        "coop_memberships",
        sa.Column(
            "membership_id",
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
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invite_code", sa.String(6), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("coop_id", "user_id", name="uq_coop_memberships_coop_user"),
    )
    op.create_index("ix_coop_memberships_user_id", "coop_memberships", ["user_id"])


def downgrade() -> None:
    op.drop_table("coop_memberships")
    op.drop_table("cooperatives")
    op.drop_table("user_roles")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS coop_status")
    op.execute("DROP TYPE IF EXISTS user_role")
