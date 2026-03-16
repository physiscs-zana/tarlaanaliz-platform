# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""KR-015: missions tablosuna sezonluk zamanlama penceresi ve atama meta alanları.

Amaç: Önceki PR'da Mission entity'sine eklenen schedule_window ve assignment
    meta alanları için DB şemasını günceller.
Sorumluluk: KR-015-2/3/4/5 (atama kaynağı, nedeni, zamanlama penceresi).
Bağımlılıklar: kr015b_reschedule.

Revision ID: kr015c_mission_schedule_fields
Revises: kr015b_reschedule
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "kr015c_mission_schedule_fields"
down_revision: Union[str, None] = "kr015b_reschedule"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # missions: KR-015-5 sezonluk zamanlama penceresi
    # -------------------------------------------------------------------------
    op.add_column(
        "missions",
        sa.Column("schedule_window_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "missions",
        sa.Column("schedule_window_end", sa.DateTime(timezone=True), nullable=True),
    )

    # -------------------------------------------------------------------------
    # missions: KR-015-2/3/4 atama kaynağı ve nedeni
    # assignment_source: SYSTEM_SEED | PULL
    # assignment_reason: AUTO_DISPATCH | ADMIN_OVERRIDE | REASSIGNMENT
    # -------------------------------------------------------------------------
    op.add_column(
        "missions",
        sa.Column(
            "assignment_source",
            sa.String(32),
            sa.CheckConstraint(
                "assignment_source IN ('SYSTEM_SEED','PULL')",
                name="ck_mission_assignment_source",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "missions",
        sa.Column(
            "assignment_reason",
            sa.String(32),
            sa.CheckConstraint(
                "assignment_reason IN ('AUTO_DISPATCH','ADMIN_OVERRIDE','REASSIGNMENT')",
                name="ck_mission_assignment_reason",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_missions_assignment_source",
        "missions",
        ["assignment_source"],
    )


def downgrade() -> None:
    op.drop_index("ix_missions_assignment_source", table_name="missions")
    op.drop_column("missions", "assignment_reason")
    op.drop_column("missions", "assignment_source")
    op.drop_column("missions", "schedule_window_end")
    op.drop_column("missions", "schedule_window_start")
