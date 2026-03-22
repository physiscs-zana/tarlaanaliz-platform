# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SQLAlchemy ORM model registry.
"""ORM model registry."""

from src.infrastructure.persistence.sqlalchemy.models.user_model import UserModel
from src.infrastructure.persistence.sqlalchemy.models.user_role_model import UserRoleModel
from src.infrastructure.persistence.sqlalchemy.models.field_model import FieldModel
from src.infrastructure.persistence.sqlalchemy.models.mission_model import MissionModel
from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel
from src.infrastructure.persistence.sqlalchemy.models.price_snapshot_model import PriceSnapshotModel
from src.infrastructure.persistence.sqlalchemy.models.pilot_model import (
    MissionAssignmentModel,
    PilotModel,
    PilotServiceAreaModel,
)
from src.infrastructure.persistence.sqlalchemy.models.expert_model import ExpertModel
from src.infrastructure.persistence.sqlalchemy.models.expert_review_model import ExpertReviewModel
from src.infrastructure.persistence.sqlalchemy.models.analysis_result_model import AnalysisResultModel
from src.infrastructure.persistence.sqlalchemy.models.analysis_job_model import AnalysisJobModel
from src.infrastructure.persistence.sqlalchemy.models.audit_log_model import AuditLogModel
from src.infrastructure.persistence.sqlalchemy.models.dataset_model import DatasetModel
from src.infrastructure.persistence.sqlalchemy.models.subscription_model import SubscriptionModel
from src.infrastructure.persistence.sqlalchemy.models.feedback_record_model import FeedbackRecordModel
from src.infrastructure.persistence.sqlalchemy.models.calibration_record_model import CalibrationRecordModel
from src.infrastructure.persistence.sqlalchemy.models.cooperative_model import (
    CooperativeModel,
    CoopInviteModel,
    CoopMembershipModel,
)
from src.infrastructure.persistence.sqlalchemy.models.qc_report_model import QCReportModel

__all__ = [
    "UserModel",
    "UserRoleModel",
    "FieldModel",
    "MissionModel",
    "PaymentIntentModel",
    "PriceSnapshotModel",
    "PilotModel",
    "PilotServiceAreaModel",
    "MissionAssignmentModel",
    "ExpertModel",
    "ExpertReviewModel",
    "AnalysisResultModel",
    "AnalysisJobModel",
    "AuditLogModel",
    "DatasetModel",
    "SubscriptionModel",
    "FeedbackRecordModel",
    "CalibrationRecordModel",
    "QCReportModel",
    "CooperativeModel",
    "CoopMembershipModel",
    "CoopInviteModel",
]
