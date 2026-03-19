# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-013: Human-readable field code for payment flows.
"""Add field_code column to fields table.

8-digit sequential code for human-readable field identification.
Replaces UUID display in payment/IBAN transfer descriptions.
Farmers (avg. age 56) need a short, easy-to-type identifier.

Revision ID: field_code_01
Revises: fields_crop_type
Create Date: 2026-03-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "field_code_01"
down_revision: Union[str, None] = "fields_crop_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sequence starting at 10000001 (always 8 digits)
    op.execute("CREATE SEQUENCE IF NOT EXISTS field_code_seq START WITH 10000001 INCREMENT BY 1 NO CYCLE")

    # Add field_code column
    op.add_column(
        "fields",
        sa.Column(
            "field_code",
            sa.String(8),
            nullable=True,
            unique=True,
            comment="8-digit human-readable field code for payment flows",
        ),
    )

    # Backfill existing fields
    op.execute("UPDATE fields SET field_code = LPAD(nextval('field_code_seq')::text, 8, '0') WHERE field_code IS NULL")

    # Now make it NOT NULL
    op.alter_column("fields", "field_code", nullable=False)

    # Set default for new inserts
    op.alter_column(
        "fields",
        "field_code",
        server_default=sa.text("LPAD(nextval('field_code_seq')::text, 8, '0')"),
    )


def downgrade() -> None:
    op.drop_column("fields", "field_code")
    op.execute("DROP SEQUENCE IF EXISTS field_code_seq")
