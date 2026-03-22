# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-065: PostGIS GIST spatial index — coverage ratio ve KR-016 eslestirme performansi.
"""Add PostGIS GIST index on fields.boundary for spatial query performance.

Revision ID: gist_001
Revises: rls_001
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "gist_001"
down_revision: Union[str, None] = "rls_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS extension kontrolu
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    # GIST index — boundary kolonu nullable, NULL degerler index'te yer almaz
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fields_boundary_gist ON fields USING GIST (boundary) WHERE boundary IS NOT NULL;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fields_boundary_gist;")
