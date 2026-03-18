# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-013: crop_type column for field crop tracking.
"""Add crop_type column to fields table.

The FieldModel ORM defines crop_type but the column was never added
to the database via migration. This caused ProgrammingError:
'column fields.crop_type does not exist' on every field operation.

Revision ID: fields_crop_type
Revises: user_ext_01
Create Date: 2026-03-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fields_crop_type"
down_revision: Union[str, None] = "user_ext_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fields", sa.Column("crop_type", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("fields", "crop_type")
