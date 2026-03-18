# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-050: display_name / expertise_tags columns for expert and pilot user profiles.
"""Add display_name and expertise_tags columns to users table.

display_name: uzman/pilot eklerken girilen ad-soyad bilgisi.
expertise_tags: uzman yetkinlik alanlari (ornek: ["PAMUK:DISEASE", "BUGDAY:PEST"]).

This migration also merges two divergent branches (kr011_ba and
kr015c_mission_schedule_fields) back into a single head.

Revision ID: user_ext_01
Revises: kr011_ba, kr015c_mission_schedule_fields
Create Date: 2026-03-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = "user_ext_01"
down_revision: tuple[str, str] = ("kr011_ba", "kr015c_mission_schedule_fields")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(160), nullable=True))
    op.add_column("users", sa.Column("expertise_tags", ARRAY(sa.String(50)), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "expertise_tags")
    op.drop_column("users", "display_name")
