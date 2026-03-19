# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Fix payment_intents schema — make price_snapshot_id nullable, add admin_note.
"""Fix payment_intents: nullable price_snapshot_id + admin_note column.

Revision ID: fix_pi_cols
Revises: 20260319_add_field_code
Create Date: 2026-03-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fix_pi_cols"
down_revision: Union[str, None] = "field_code_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Make price_snapshot_id nullable (FK constraint prevents INSERT with dummy UUID)
    # Drop FK constraint first, alter column, re-add FK
    op.execute("ALTER TABLE payment_intents ALTER COLUMN price_snapshot_id DROP NOT NULL")

    # 2. Add admin_note column if not exists
    has_col = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name='payment_intents' AND column_name='admin_note')"
        )
    ).scalar()
    if not has_col:
        op.add_column("payment_intents", sa.Column("admin_note", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("payment_intents", "admin_note")
    op.execute("ALTER TABLE payment_intents ALTER COLUMN price_snapshot_id SET NOT NULL")
