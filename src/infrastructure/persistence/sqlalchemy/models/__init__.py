# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SQLAlchemy ORM model registry.
"""ORM model registry — import all models so Base.metadata knows about them."""

from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel

__all__ = ["UserModel", "FieldModel"]
