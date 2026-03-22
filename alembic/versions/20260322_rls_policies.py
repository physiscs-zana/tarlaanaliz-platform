# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-066: Row-Level Security — pipeline_rw rolunun PII tablolarina erisimini engelle.
# KR-070: Worker isolation — veri pipeline rolu PII goremez.
"""Add RLS policies to protect PII tables from pipeline_rw role.

Revision ID: rls_001
Revises: datasets_001
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "rls_001"
down_revision: Union[str, None] = "datasets_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# KR-066: PII tablolari — pipeline_rw erisimi engellenir
_PII_TABLES = ["users", "user_roles", "coop_memberships", "payment_intents"]


def upgrade() -> None:
    # pipeline_rw rolu yoksa olustur (IF NOT EXISTS)
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pipeline_rw') THEN CREATE ROLE pipeline_rw; END IF; END $$;"
    )

    for table in _PII_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"DO $$ BEGIN "
            f"IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'pipeline_deny_{table}') THEN "
            f"CREATE POLICY pipeline_deny_{table} ON {table} FOR ALL TO pipeline_rw USING (false); "
            f"END IF; END $$;"
        )


def downgrade() -> None:
    for table in reversed(_PII_TABLES):
        op.execute(f"DROP POLICY IF EXISTS pipeline_deny_{table} ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
