# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Weather Block status basitleştirme — KR-015-3A.

KR-015-3A: Pilot sahada tek yetkili; admin doğrulama akışı kaldırıldı.
PENDING → REPORTED, CONFIRMED → REPORTED, VERIFIED → REPORTED, REJECTED → EXPIRED.
verified_by_admin_id ve verified_at sütunları nullable yapılır (veri korunur, yeni kayıt yazılmaz).

Revision ID: kr015_3a
Revises: wbr001
Create Date: 2026-03-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "kr015_3a"
down_revision: Union[str, None] = "wbr001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Mevcut verileri yeni durumlara migrate et
    op.execute("""
        UPDATE weather_block_reports
        SET status = 'REPORTED'
        WHERE status IN ('PENDING', 'CONFIRMED', 'VERIFIED')
    """)
    op.execute("""
        UPDATE weather_block_reports
        SET status = 'EXPIRED'
        WHERE status = 'REJECTED'
    """)

    # 2. Eski CHECK constraint kaldır
    op.drop_constraint("ck_wbr_status", "weather_block_reports", type_="check")

    # 3. Yeni CHECK constraint ekle (KR-015-3A sadeleştirilmiş durumlar)
    op.create_check_constraint(
        "ck_wbr_status",
        "weather_block_reports",
        "status IN ('REPORTED', 'EXPIRED', 'RESOLVED')",
    )

    # 4. verified_by_admin_id ve verified_at artık kullanılmıyor ama veri korunur
    # Sütunları nullable yap (zaten nullable olan verified_at için noop)
    op.alter_column(
        "weather_block_reports",
        "verified_by_admin_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    # CHECK constraint geri al
    op.drop_constraint("ck_wbr_status", "weather_block_reports", type_="check")
    op.create_check_constraint(
        "ck_wbr_status",
        "weather_block_reports",
        "status IN ('REPORTED', 'VERIFIED', 'RESOLVED', 'REJECTED')",
    )

    # REPORTED → PENDING geri dönüş
    op.execute("""
        UPDATE weather_block_reports
        SET status = 'PENDING'
        WHERE status = 'REPORTED'
    """)
