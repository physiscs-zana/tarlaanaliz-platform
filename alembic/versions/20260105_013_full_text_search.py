# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: Full-text search indexes — deferred to post-launch.
"""Full-text search indexes — DEFERRED.

GIN/trigram indexes for text search. Not needed for initial launch
with ~1500 users. Will be implemented after production schema stabilizes.

Revision ID: 013
Revises: 012
Create Date: 2026-01-05
"""

from typing import Sequence, Union

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: full-text search deferred to post-launch."""
    pass


def downgrade() -> None:
    """No-op."""
    pass
