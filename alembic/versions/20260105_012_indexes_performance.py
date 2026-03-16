# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Performance indexes — deferred to post-launch.
"""Performance indexes — DEFERRED.

These indexes optimize query performance for large datasets.
For the initial launch (~1500 users), they are not needed.
They will be re-implemented with verified column names after
the first month of production operation.

Revision ID: 012
Revises: 011
Create Date: 2026-01-05
"""

from typing import Sequence, Union

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: performance indexes deferred to post-launch."""
    pass


def downgrade() -> None:
    """No-op."""
    pass
