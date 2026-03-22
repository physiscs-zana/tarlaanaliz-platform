# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015: RescheduleRequest re-export — deprecated scaffold, gerçek model sqlalchemy/models/ altında.
# Gerçek ORM modeli: src/infrastructure/persistence/sqlalchemy/models/reschedule_request_model.py
# Eski import'lar için re-export:
from src.infrastructure.persistence.sqlalchemy.models.reschedule_request_model import (
    RescheduleRequestModel,
)

__all__ = ["RescheduleRequestModel"]
