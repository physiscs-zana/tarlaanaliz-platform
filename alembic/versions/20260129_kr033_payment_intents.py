# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-033 Ödeme ve Manuel Onay Akışı tabloları.

Amaç: payment_intents tablosunu oluşturmak; missions ve subscriptions tablolarına
    payment_intent_id referansı eklemek.
Sorumluluk: Ödeme akışı altyapısı — kredi kartı ve IBAN havale desteği.
Güvenlik: Ödeme durumu (PAID/PENDING) kritik güvenlik alanıdır.
    PAID statüsü olmadan Mission ASSIGNED olamaz (KR-033 hard gate).
Bağımlılıklar: 013 (full_text_search) migration'ının tamamlanmış olması.
    users, missions, subscriptions tablolarının mevcut olması.

Revision ID: kr033
Revises: 013
Create Date: 2026-01-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "kr033"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # payment_intents tablosu
    # -------------------------------------------------------------------------
    op.create_table(
        "payment_intents",
        sa.Column("payment_intent_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payer_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "coop_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "target_type",
            sa.String(20),
            sa.CheckConstraint("target_type IN ('MISSION', 'SUBSCRIPTION')", name="ck_pi_target_type"),
            nullable=False,
        ),
        sa.Column("target_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_kurus", sa.BigInteger, nullable=False),
        sa.Column("currency", sa.String(3), server_default="TRY", nullable=False),
        sa.Column(
            "method",
            sa.String(20),
            sa.CheckConstraint("method IN ('CREDIT_CARD', 'IBAN_TRANSFER')", name="ck_pi_method"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            sa.CheckConstraint(
                "status IN ('PAYMENT_PENDING', 'PAID', 'REJECTED', 'EXPIRED', 'CANCELLED', 'REFUNDED')",
                name="ck_pi_status",
            ),
            nullable=False,
            server_default="PAYMENT_PENDING",
        ),
        sa.Column("payment_ref", sa.String(50), unique=True, nullable=False),
        sa.Column(
            "price_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("price_snapshots.price_snapshot_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Ödeme sağlayıcı bilgileri
        sa.Column("provider", sa.String(30), nullable=True),
        sa.Column("provider_session_id", sa.String(255), nullable=True),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        # Dekont bilgileri (IBAN havale için)
        sa.Column("receipt_blob_id", sa.String(255), nullable=True),
        sa.Column("receipt_meta", sa.dialects.postgresql.JSONB, nullable=True),
        # Onay bilgileri
        sa.Column(
            "approved_by_admin_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        # Red bilgileri
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_reason", sa.Text, nullable=True),
        # İptal bilgileri
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text, nullable=True),
        # İade bilgileri
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_amount_kurus", sa.BigInteger, nullable=True),
        sa.Column("refund_reason", sa.Text, nullable=True),
        # Süre sonu (IBAN transferleri için 7 gün)
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        # Zaman damgaları
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # -------------------------------------------------------------------------
    # missions tablosuna payment_intent_id FK ekle (sütun yoksa)
    # -------------------------------------------------------------------------
    conn = op.get_bind()
    has_col = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='missions' AND column_name='payment_intent_id')"
    )).scalar()
    if not has_col:
        op.add_column(
            "missions",
            sa.Column(
                "payment_intent_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("payment_intents.payment_intent_id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    # -------------------------------------------------------------------------
    # subscriptions tablosuna payment_intent_id FK ekle (sütun yoksa)
    # -------------------------------------------------------------------------
    has_col2 = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='subscriptions' AND column_name='payment_intent_id')"
    )).scalar()
    if not has_col2:
        op.add_column(
            "subscriptions",
            sa.Column(
                "payment_intent_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("payment_intents.payment_intent_id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    # FK sütunlarını kaldır
    op.drop_column("subscriptions", "payment_intent_id")
    op.drop_column("missions", "payment_intent_id")

    # payment_intents tablosunu kaldır
    op.drop_table("payment_intents")
