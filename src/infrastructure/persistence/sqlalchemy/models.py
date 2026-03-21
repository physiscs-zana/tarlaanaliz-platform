# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/infrastructure/persistence/sqlalchemy/models.py
# DESC: Model registry — tum ORM modellerini import eder. Alembic autogenerate icin gerekli.
"""
Model registry.

Bu modul tum ORM modellerini import ederek Base.metadata'ya kaydeder.
Alembic autogenerate bu modulu kullanarak tablo degisikliklerini tespit eder.
"""

from src.infrastructure.persistence.sqlalchemy.base import Base  # noqa: F401

# Core models
from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.pilot_model import PilotModel, PilotServiceAreaModel, MissionAssignmentModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.price_snapshot_model import PriceSnapshotModel  # noqa: F401

# Analysis & review models
from src.infrastructure.persistence.sqlalchemy.models.analysis_result_model import AnalysisResultModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.expert_model import ExpertModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.expert_review_model import ExpertReviewModel  # noqa: F401
from src.infrastructure.persistence.sqlalchemy.models.dataset_model import DatasetModel  # noqa: F401

# Audit log model (WORM — BOLUM 3, KR-062)
from src.infrastructure.persistence.sqlalchemy.repositories.audit_log_repository_impl import AuditLogModel  # noqa: F401
