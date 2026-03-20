# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: Extend payment_intents status CHECK to include PENDING_ADMIN_REVIEW, PENDING_RECEIPT.
"""Extend ck_pi_status CHECK constraint with PENDING_ADMIN_REVIEW and PENDING_RECEIPT.

These statuses are used by admin SLA calculations and receipt workflow but were
missing from the original CHECK constraint, causing INSERT failures.

Revision ID: extend_pi_status
Revises: fix_pi_cols
Create Date: 2026-03-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "extend_pi_status"
down_revision: Union[str, None] = "fix_pi_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE payment_intents DROP CONSTRAINT IF EXISTS ck_pi_status")
    op.execute(
        "ALTER TABLE payment_intents ADD CONSTRAINT ck_pi_status "
        "CHECK (status IN ("
        "'PAYMENT_PENDING', 'PENDING_RECEIPT', 'PENDING_ADMIN_REVIEW', "
        "'PAID', 'REJECTED', 'EXPIRED', 'CANCELLED', 'REFUNDED'"
        "))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE payment_intents DROP CONSTRAINT IF EXISTS ck_pi_status")
    op.execute(
        "ALTER TABLE payment_intents ADD CONSTRAINT ck_pi_status "
        "CHECK (status IN ("
        "'PAYMENT_PENDING', 'PAID', 'REJECTED', 'EXPIRED', 'CANCELLED', 'REFUNDED'"
        "))"
    )
