# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""BILLING_ADMIN rolü ekleme — KR-011.

SSOT KR-011: Ödeme Yöneticisi (BILLING_ADMIN) — IBAN dekont onayı, geri ödeme,
kar payı raporlama; limit üstünde CENTRAL_ADMIN'e eskalasyon.

Revision ID: kr011_ba
Revises: kr015_3a
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "kr011_ba"
down_revision: Union[str, None] = "kr015_3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL enum tip genişletme — user_roles enum'a BILLING_ADMIN ekle
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'BILLING_ADMIN'")


def downgrade() -> None:
    # PostgreSQL enum'dan değer kaldırmak karmaşıktır ve genellikle desteklenmez.
    # Downgrade durumunda mevcut BILLING_ADMIN kullanıcıları kontrol edilmelidir.
    pass
