# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Add display_name and expertise_tags columns to users table.

display_name: uzman/pilot eklerken girilen ad-soyad bilgisi.
expertise_tags: uzman yetkinlik alanlari (ornek: ["PAMUK:DISEASE", "BUGDAY:PEST"]).

Revision ID: user_ext_01
Revises: kr011_ba
Create Date: 2026-03-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = "user_ext_01"
down_revision: Union[str, None] = "kr011_ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(160), nullable=True))
    op.add_column("users", sa.Column("expertise_tags", ARRAY(sa.String(50)), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "expertise_tags")
    op.drop_column("users", "display_name")
