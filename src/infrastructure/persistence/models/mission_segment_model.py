# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: MissionSegment re-export — deprecated scaffold, gerçek model sqlalchemy/models/ altında.
# Gerçek ORM modeli: src/infrastructure/persistence/sqlalchemy/models/mission_segment_model.py
# Eski import'lar için re-export:
from src.infrastructure.persistence.sqlalchemy.models.mission_segment_model import (
    MissionSegmentModel,
)

__all__ = ["MissionSegmentModel"]
